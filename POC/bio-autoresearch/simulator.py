"""
Fixed evaluation harness for bio-autoresearch. DO NOT MODIFY.

GP surrogate trained on real V. natriegens growth data from Monomer Bio hackathon.
Predicts growth rates for media compositions and adds biological noise.

Usage (by the agent's recipe.py):
    from simulator import evaluate_recipes
    results = evaluate_recipes(recipes)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Search space bounds (g/L)
SEARCH_SPACE = {
    "nacl_g_l":           (10.0, 35.0),
    "glucose_g_l":        (1.0, 20.0),
    "yeast_extract_g_l":  (2.0, 10.0),
}

# Fixed components
FIXED = {
    "tryptone_g_l": 10.0,
    "mops_ph": 7.0,
}

# Noise and evaluation
NOISE_STD = 0.08
N_REPLICATES = 3
MAX_RECIPES_PER_ROUND = 14

# ---------------------------------------------------------------------------
# GP Surrogate
# ---------------------------------------------------------------------------

_gp: GaussianProcessRegressor | None = None
_scaler: StandardScaler | None = None
_vol_cols: list[str] = []
_rng = np.random.default_rng(42)


def _fit_gp() -> None:
    """Train GP on all available historical plate data."""
    global _gp, _scaler, _vol_cols

    reagent_cols = [
        "base_media_vol", "yeast_extract", "tryptone",
        "mops", "na_l_glut", "kh2po4", "glucose",
    ]

    growth_files = sorted(DATA_DIR.glob("*_growth.csv"))
    all_rows = []
    for gf in growth_files:
        prefix = gf.name.replace("_growth.csv", "")
        mf = DATA_DIR / f"{prefix}_plate_condition_map.csv"
        if not mf.exists():
            continue
        growth = pd.read_csv(gf)
        maps = pd.read_csv(mf)
        merged = growth[["well", "growth_rate_per_hr"]].merge(maps, on="well", how="inner")
        all_rows.append(merged)

    if not all_rows:
        print("WARNING: No historical data found. Using random surrogate.")
        return

    df = pd.concat(all_rows, ignore_index=True)
    _vol_cols = [c for c in reagent_cols if c in df.columns]
    X = df[_vol_cols].fillna(0).values.astype(float)
    y = df["growth_rate_per_hr"].values.astype(float)

    if len(X) < 2:
        return

    _scaler = StandardScaler()
    _scaler.fit(X)
    X_scaled = _scaler.transform(X)

    kernel = ConstantKernel(1.0) * Matern(nu=2.5) + WhiteKernel(noise_level=0.01)
    _gp = GaussianProcessRegressor(
        kernel=kernel, n_restarts_optimizer=5,
        normalize_y=True, random_state=42,
    )
    _gp.fit(X_scaled, y)
    print(f"GP surrogate trained on {len(X)} observations from {len(growth_files)} plates.")


def predict_growth_rate(nacl_g_l: float, glucose_g_l: float, yeast_extract_g_l: float) -> float:
    """Predict growth rate (h^-1) for a single media composition. Includes biological noise."""
    if _gp is None:
        return 0.8 + _rng.normal(0, NOISE_STD)

    # Map g/L concentrations to approximate uL volumes (for GP trained on volume data)
    # Stock concentrations: YE 100 mg/mL, Glucose 100 mg/mL, NaCl 5M (292.2 g/mol)
    ye_ul = (yeast_extract_g_l / 100) * 200
    glucose_ul = (glucose_g_l / 100) * 200
    nacl_ul = (nacl_g_l / 292.2) / 5.0 * 200 * 1000  # g/L -> mM -> uL

    x_dict = {c: 0.0 for c in _vol_cols}
    if "yeast_extract" in x_dict:
        x_dict["yeast_extract"] = ye_ul
    if "glucose" in x_dict:
        x_dict["glucose"] = glucose_ul

    x = np.array([[x_dict.get(c, 0.0) for c in _vol_cols]])
    x_scaled = _scaler.transform(x)
    mu, std = _gp.predict(x_scaled, return_std=True)
    rate = float(mu[0]) + _rng.normal(0, NOISE_STD)
    return max(0.1, rate)


def evaluate_recipes(recipes: list[dict]) -> dict:
    """
    Evaluate a batch of media recipes. Each recipe is a dict with keys:
        nacl_g_l, glucose_g_l, yeast_extract_g_l

    Returns dict with:
        results: list of {recipe, mean_growth_rate, std, replicates}
        best_rate: float
        best_recipe: dict
    """
    if len(recipes) > MAX_RECIPES_PER_ROUND:
        return {"error": f"Too many recipes: {len(recipes)} > {MAX_RECIPES_PER_ROUND}"}

    # Validate bounds
    for i, r in enumerate(recipes):
        for key, (lo, hi) in SEARCH_SPACE.items():
            val = r.get(key, 0)
            if val < lo or val > hi:
                return {"error": f"Recipe {i}: {key}={val} out of bounds [{lo}, {hi}]"}

    results = []
    for r in recipes:
        replicates = []
        for _ in range(N_REPLICATES):
            rate = predict_growth_rate(r["nacl_g_l"], r["glucose_g_l"], r["yeast_extract_g_l"])
            replicates.append(round(rate, 4))
        mean_rate = round(float(np.mean(replicates)), 4)
        std_rate = round(float(np.std(replicates)), 4)
        results.append({
            "recipe": r,
            "mean_growth_rate": mean_rate,
            "std": std_rate,
            "replicates": replicates,
        })

    # Sort by mean growth rate descending
    results.sort(key=lambda x: x["mean_growth_rate"], reverse=True)
    best = results[0]

    return {
        "n_recipes": len(results),
        "results": results,
        "best_rate": best["mean_growth_rate"],
        "best_recipe": best["recipe"],
    }


# ---------------------------------------------------------------------------
# Baseline recipe (control)
# ---------------------------------------------------------------------------

BASELINE_RECIPE = {
    "nacl_g_l": 10.0,
    "glucose_g_l": 0.0,  # clamped to min
    "yeast_extract_g_l": 5.0,
}

# Initialize GP on import
_fit_gp()

# ---------------------------------------------------------------------------
# Main — run baseline if executed directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Clamp baseline glucose to search space min
    baseline = {**BASELINE_RECIPE, "glucose_g_l": max(1.0, BASELINE_RECIPE["glucose_g_l"])}
    result = evaluate_recipes([baseline])
    print("--- Baseline ---")
    print(f"Recipe:      {baseline}")
    print(f"Growth rate: {result['best_rate']} h^-1")
    print(f"Replicates:  {result['results'][0]['replicates']}")
    print(f"\nSearch space: {SEARCH_SPACE}")
    print(f"Fixed:        {FIXED}")
