#!/usr/bin/env python3
"""
baybe_opt.py — Bayesian optimization workflow for V. natriegens growth media.

Loads historical plate data, runs per-base-media BayBE campaigns, annotates
proposals with a sklearn GP surrogate prediction, and writes results in
*_plate_condition_map.csv format with an added predicted_growth_rate_per_hr column.

Volume constraint: base_media_vol + reagents + cells + water = 200 µL
  → BayBE enforces: base_media_vol + sum(reagents) + cells ≤ 200 µL
  → water fills the remainder, always ≥ 0
  → cells is an optimizable parameter (not fixed)

Usage:
    python scripts/baybe_opt.py                         # defaults
    python scripts/baybe_opt.py --round 3 --n-proposals 20
    python scripts/baybe_opt.py --data-dir data --output results/round3.csv
    python scripts/baybe_opt.py --media "Semi-Defined Media" "High Buffer Defined Media"
"""

from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from baybe import Campaign
from baybe.constraints import ContinuousLinearConstraint
from baybe.objectives import SingleTargetObjective
from baybe.parameters import NumericalContinuousParameter
from baybe.recommenders import BotorchRecommender, RandomRecommender
from baybe.searchspace import SearchSpace
from baybe.targets import NumericalTarget

# ── Constants ──────────────────────────────────────────────────────────────────

TOTAL_VOL_UL = 200

# Reagent columns match _plate_condition_map.csv headers exactly
REAGENT_COLS = [
    "yeast_extract", "tryptone", "mops", "na_l_glut", "kh2po4", "glucose",
    # Round 2 additions (mechanistic hypothesis conditions)
    "mgso4", "trace_metals", "glycerol", "feso4", "nacit",
]
# ALL_VOL_COLS: all parameters optimized by BayBE (cells is now included)
ALL_VOL_COLS = ["base_media_vol"] + REAGENT_COLS + ["cells"]

# Volume bounds (µL) — must cover the full range present in historical data
BASE_MEDIA_VOL_BOUNDS = (100, 190)  # second plate tested up to 190 µL
REAGENT_VOL_BOUNDS = (0, 40)        # per-reagent cap; historical max was ~26 µL
CELL_VOL_BOUNDS = (10, 100)         # second plate tested 10–100 µL inoculum
MAX_REAGENT_SUM_UL = 60             # total additive volume across active reagents
MIN_WATER_UL = 10                   # minimum water to reserve for dilution

# Tighter per-reagent bounds for specialty supplements introduced in round 2.
# These are biologically active at low doses; cap well below REAGENT_VOL_BOUNDS.
SPECIALTY_REAGENT_BOUNDS: dict[str, tuple[float, float]] = {
    "mgso4":       (0, 15),   # magnesium sulfate; tested at 4 µL
    "trace_metals": (0, 15),  # trace metal mix; tested at 4 µL
    "glycerol":    (0, 50),   # carbon-source supplement; tested at 36 µL
    "feso4":       (0, 15),   # iron sulfate; tested at 4 µL
    "nacit":       (0, 15),   # sodium citrate; tested at 4 µL
}

BASE_MEDIA_OPTIONS = [
    "Novel Bio NBxCyclone Media",
    "Prepared LBv2 Media",
    "Defined-Minimal Media",
    "Semi-Defined Media",
    "High Buffer Defined Media",
    "Defined Glycerol Media",
]

TARGET_COL = "mean_growth_rate_per_hr"
RANDOM_SEED = 42

# Campaign design
N_TOP_MEDIA = 2       # how many base media to run campaigns for
N_ACTIVE_REAGENTS = 3  # reagents to vary per campaign (others fixed at 0)


# ── Data loading ───────────────────────────────────────────────────────────────

def load_history(data_dir: str | Path) -> pd.DataFrame:
    """
    Build training data by joining *_growth.csv (per-well growth rates) to
    *_plate_condition_map.csv (per-well volumes) on the `well` column.

    A composition fingerprint is created from (base_media, all volume columns) so
    that replicate wells sharing the same recipe are averaged together, and
    identical compositions that appear across multiple plates are also merged.
    This avoids any reliance on condition naming conventions.

    Returns one row per unique composition with mean growth rate.
    """
    data_dir = Path(data_dir)

    growth_by_plate = {
        f.name.replace("_growth.csv", ""): f
        for f in sorted(data_dir.glob("*_growth.csv"))
    }
    map_by_plate = {
        f.name.replace("_plate_condition_map.csv", ""): f
        for f in sorted(data_dir.glob("*_plate_condition_map.csv"))
    }

    plate_ids = sorted(set(growth_by_plate) & set(map_by_plate))
    if not plate_ids:
        raise FileNotFoundError(
            f"No matching *_growth.csv / *_plate_condition_map.csv pairs in {data_dir}"
        )

    all_rows: list[pd.DataFrame] = []
    for plate_id in plate_ids:
        growth = pd.read_csv(growth_by_plate[plate_id])
        maps = pd.read_csv(map_by_plate[plate_id])

        vol_cols = [c for c in ALL_VOL_COLS if c in maps.columns]

        merged = growth[["well", "growth_rate_per_hr"]].merge(
            maps[["well", "base_media"] + vol_cols],
            on="well",
            how="inner",
        ).dropna(subset=["growth_rate_per_hr"])

        merged = merged.rename(columns={"growth_rate_per_hr": TARGET_COL})
        all_rows.append(merged[["base_media"] + vol_cols + [TARGET_COL]])

    combined = pd.concat(all_rows, ignore_index=True)

    # Aggregate replicates: group by unique composition (media + volumes)
    vol_cols_all = [c for c in ALL_VOL_COLS if c in combined.columns]
    combined = (
        combined.groupby(["base_media"] + vol_cols_all, as_index=False)[TARGET_COL].mean()
    )

    return combined.reset_index(drop=True)


# ── GP surrogate for growth-rate predictions ───────────────────────────────────

class GrowthRatePredictor:
    """
    Thin sklearn GP wrapper that one-hot encodes base_media and scales volumes
    before fitting/predicting. Used only to annotate proposed conditions with a
    predicted growth rate — BayBE uses its own internal surrogate for acquisition.
    """

    def __init__(self) -> None:
        kernel = ConstantKernel(1.0) * Matern(nu=2.5) + WhiteKernel(noise_level=0.01)
        self._gp = GaussianProcessRegressor(
            kernel=kernel,
            n_restarts_optimizer=5,
            normalize_y=True,
            random_state=RANDOM_SEED,
        )
        self._ohe = OneHotEncoder(handle_unknown="ignore")
        self._scaler = StandardScaler()
        self._fitted = False

    def _featurize(self, df: pd.DataFrame) -> np.ndarray:
        media_enc = self._ohe.transform(df[["base_media"]])
        if hasattr(media_enc, "toarray"):
            media_enc = media_enc.toarray()
        vols = self._scaler.transform(df[self._vol_cols])
        return np.hstack([media_enc, vols])

    def fit(self, df: pd.DataFrame) -> "GrowthRatePredictor":
        self._vol_cols = [c for c in ALL_VOL_COLS if c in df.columns]
        self._ohe.fit(df[["base_media"]])
        self._scaler.fit(df[self._vol_cols])
        X = self._featurize(df)
        y = df[TARGET_COL].values
        self._gp.fit(X, y)
        self._fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            return np.full(len(df), np.nan)
        X = self._featurize(df)
        return self._gp.predict(X)


# ── Media and reagent selection ────────────────────────────────────────────────

def select_top_media(history: pd.DataFrame, n: int = N_TOP_MEDIA) -> list[str]:
    """Return the top N base media ranked by mean growth rate in history."""
    return (
        history.groupby("base_media")[TARGET_COL]
        .mean()
        .sort_values(ascending=False)
        .head(n)
        .index.tolist()
    )


def select_active_reagents(
    media_history: pd.DataFrame,
    n: int = N_ACTIVE_REAGENTS,
) -> list[str]:
    """
    Pick the top N reagents to vary for a given media campaign.

    Reagents are ranked by absolute correlation with growth rate across the
    historical conditions for this media. Reagents with zero variance (never
    varied in the data) get correlation 0 and are ranked last. Falls back to
    the first N reagents in REAGENT_COLS when there is insufficient data to
    compute correlations.
    """
    if len(media_history) < 2:
        return REAGENT_COLS[:n]

    correlations: dict[str, float] = {}
    for col in REAGENT_COLS:
        if media_history[col].std() > 1e-6:
            corr = media_history[col].corr(media_history[TARGET_COL])
            correlations[col] = abs(corr) if pd.notna(corr) else 0.0
        else:
            correlations[col] = 0.0

    return sorted(correlations, key=correlations.get, reverse=True)[:n]


# ── BayBE campaign per base media ─────────────────────────────────────────────

def _make_searchspace(active_reagents: list[str]) -> SearchSpace:
    """
    Build a BayBE SearchSpace for base_media_vol, the active reagents, and cells.
    Linear budget constraint: sum of optimized volumes ≤ TOTAL_VOL_UL (water fills rest).
    """
    opt_cols = ["base_media_vol"] + active_reagents + ["cells"]
    parameters = [
        NumericalContinuousParameter("base_media_vol", bounds=BASE_MEDIA_VOL_BOUNDS),
        *[
            NumericalContinuousParameter(
                col, bounds=SPECIALTY_REAGENT_BOUNDS.get(col, REAGENT_VOL_BOUNDS)
            )
            for col in active_reagents
        ],
        NumericalContinuousParameter("cells", bounds=CELL_VOL_BOUNDS),
    ]
    constraints = [
        # Overall budget: leave at least MIN_WATER_UL for water
        ContinuousLinearConstraint(
            parameters=opt_cols,
            operator="<=",
            coefficients=[1.0] * len(opt_cols),
            rhs=float(TOTAL_VOL_UL - MIN_WATER_UL),
        ),
        # Reagent cap: keep additive volumes at a biologically reasonable scale
        ContinuousLinearConstraint(
            parameters=active_reagents,
            operator="<=",
            coefficients=[1.0] * len(active_reagents),
            rhs=float(MAX_REAGENT_SUM_UL),
        ),
    ]
    return SearchSpace.from_product(parameters=parameters, constraints=constraints)


def _run_media_campaign(
    media: str,
    media_history: pd.DataFrame,
    active_reagents: list[str],
    n: int,
) -> pd.DataFrame:
    """
    Run a BayBE campaign for one base-media type varying only the active reagents.

    Inactive reagents are fixed at 0 in the output. Uses BotorchRecommender
    when training data is available, RandomRecommender otherwise.
    """
    opt_cols = ["base_media_vol"] + active_reagents + ["cells"]

    has_data = not media_history.empty
    recommender = BotorchRecommender() if has_data else RandomRecommender()

    campaign = Campaign(
        searchspace=_make_searchspace(active_reagents),
        objective=SingleTargetObjective(NumericalTarget(name=TARGET_COL, mode="MAX")),
        recommender=recommender,
    )

    if has_data:
        # Pass only the optimized columns so the search space matches
        measurements = media_history[opt_cols + [TARGET_COL]].copy()
        campaign.add_measurements(measurements)

    recs = campaign.recommend(batch_size=n).copy()
    recs["base_media"] = media

    # Round optimized volumes
    for col in opt_cols:
        recs[col] = recs[col].clip(lower=0).round(1)

    # Fix all inactive reagents at 0
    for col in REAGENT_COLS:
        if col not in active_reagents:
            recs[col] = 0.0

    vol_sum = recs[opt_cols].sum(axis=1)
    recs["water"] = (TOTAL_VOL_UL - vol_sum).clip(lower=0).round(1)
    recs["total"] = TOTAL_VOL_UL

    return recs.reset_index(drop=True)


# ── Multi-campaign orchestration ───────────────────────────────────────────────

def propose_conditions(
    history: pd.DataFrame,
    n_proposals: int = 20,
    n_media: int = N_TOP_MEDIA,
    n_reagents: int = N_ACTIVE_REAGENTS,
) -> pd.DataFrame:
    """
    Select the top-performing base media, run a focused BayBE campaign for each
    (varying only its most informative reagents), and return combined proposals.

    Proposal slots are split evenly across the selected media.
    """
    media_list = select_top_media(history, n=n_media) if not history.empty else BASE_MEDIA_OPTIONS[:n_media]

    n_per_media = max(1, n_proposals // len(media_list))
    # Give any remainder to the top media
    remainder = n_proposals - n_per_media * len(media_list)
    allocations = {m: n_per_media for m in media_list}
    allocations[media_list[0]] += remainder

    all_recs: list[pd.DataFrame] = []
    for media, n_alloc in allocations.items():
        media_history = history[history["base_media"] == media].copy()
        active = select_active_reagents(media_history, n=n_reagents)
        try:
            recs = _run_media_campaign(media, media_history, active, n_alloc)
            all_recs.append(recs)
            print(f"    [{media}] {len(media_history)} obs, reagents: {active} → {n_alloc} proposals")
        except Exception as exc:
            warnings.warn(f"Campaign failed for {media!r}: {exc}")

    if not all_recs:
        raise RuntimeError("All campaigns failed — cannot generate proposals.")

    return pd.concat(all_recs, ignore_index=True)


# ── Output formatting ──────────────────────────────────────────────────────────

def format_output(
    proposals: pd.DataFrame,
    predicted: np.ndarray,
    round_num: int | None = None,
) -> pd.DataFrame:
    """
    Format proposals to match *_plate_condition_map.csv column order, sorted by
    predicted growth rate (descending), with an added predicted_growth_rate_per_hr
    column. Condition names are assigned after sorting (Rank-1, Rank-2, …).
    """
    prefix = f"R{round_num}-" if round_num else "Proposal-"
    n = len(proposals)

    out = pd.DataFrame({
        "condition":                    [f"{prefix}{i+1}" for i in range(n)],
        "base_media":                   proposals["base_media"].values,
        "base_media_vol":               proposals["base_media_vol"].values,
        "yeast_extract":                proposals["yeast_extract"].values,
        "tryptone":                     proposals["tryptone"].values,
        "mops":                         proposals["mops"].values,
        "na_l_glut":                    proposals["na_l_glut"].values,
        "kh2po4":                       proposals["kh2po4"].values,
        "glucose":                      proposals["glucose"].values,
        "mgso4":                        proposals["mgso4"].values,
        "trace_metals":                 proposals["trace_metals"].values,
        "glycerol":                     proposals["glycerol"].values,
        "feso4":                        proposals["feso4"].values,
        "nacit":                        proposals["nacit"].values,
        "water":                        proposals["water"].values,
        "cells":                        proposals["cells"].values,
        "total":                        proposals["total"].values,
        "predicted_growth_rate_per_hr": np.round(predicted, 4),
    })

    out = out.sort_values(
        "predicted_growth_rate_per_hr", ascending=False, na_position="last"
    ).reset_index(drop=True)

    # Re-number conditions by rank after sorting
    out["condition"] = [f"{prefix}{i+1}" for i in range(n)]

    return out


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="BayBE Bayesian optimization for V. natriegens growth media",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir", default="data",
        help="Directory containing *_replicates.csv and *_plate_condition_map.csv files",
    )
    parser.add_argument(
        "--n-proposals", type=int, default=20,
        help="Total number of conditions to propose",
    )
    parser.add_argument(
        "--round", type=int, default=None,
        help="Round number used in condition name prefix (e.g. 3 → R3-1, R3-2, …)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output CSV path (default: bo_outputs/next_round_plate_condition_map.csv)",
    )
    parser.add_argument(
        "--n-media", type=int, default=N_TOP_MEDIA,
        help="Number of top-performing base media to run campaigns for",
    )
    parser.add_argument(
        "--n-reagents", type=int, default=N_ACTIVE_REAGENTS,
        help="Number of reagents to vary per campaign (others fixed at 0)",
    )
    args = parser.parse_args()

    np.random.seed(RANDOM_SEED)

    # 1. Load historical data
    print(f"Loading historical data from {args.data_dir!r} ...")
    history = load_history(args.data_dir)
    print(f"  {len(history)} unique conditions across {history['base_media'].nunique()} media type(s)")
    print(f"  Growth rate range: {history[TARGET_COL].min():.3f} – {history[TARGET_COL].max():.3f} h⁻¹")

    # 2. Fit GP surrogate for annotating predicted growth rates
    predictor = GrowthRatePredictor()
    if len(history) >= 2:
        predictor.fit(history)
        print("  GP surrogate fitted.")
    else:
        print("  Warning: fewer than 2 observations — GP predictions will be NaN.")

    # 3. Run focused BayBE campaigns for top media
    print(f"\nRunning BayBE campaigns ({args.n_proposals} proposals, top {args.n_media} media, {args.n_reagents} reagents each) ...")
    proposals = propose_conditions(
        history,
        n_proposals=args.n_proposals,
        n_media=args.n_media,
        n_reagents=args.n_reagents,
    )

    # 4. Annotate with GP surrogate predictions
    predicted = predictor.predict(proposals) if predictor._fitted else np.full(len(proposals), np.nan)

    # 5. Format and save
    output_df = format_output(proposals, predicted, round_num=args.round)

    output_path = args.output or "bo_outputs/next_round_plate_condition_map.csv"
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    output_df.to_csv(output_path, index=False)

    print(f"\nSaved {len(output_df)} proposals → {output_path!r}")
    print("\nTop proposals:")
    display_cols = ["condition", "base_media", "base_media_vol", "predicted_growth_rate_per_hr"]
    print(output_df[display_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
