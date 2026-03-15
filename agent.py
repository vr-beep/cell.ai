"""
Monomer Bio Hackathon - Track A
Closed-Loop Bayesian Optimization Agent (phase-2 focused)

This version is modified for a two-stage workflow:
- Phase 1 screens many factors externally and identifies the top 3 drivers.
- Phase 2 Bayesian optimization only searches those top 3 factors.
- All other media components are held constant at safe / effective values.

Optimizer: BayBE (Bayesian optimization library) for rounds 2+.
Key improvements:
- Logical separation between optimized factors and fixed constants
- Plate randomization with control spreading to reduce spatial bias
- pH adjustment uses calibration lookup + interpolation before linear fallback
- Replicates are aggregated before model fitting
- BayBE TwoPhaseMetaRecommender: FPS for initial, BotorchRecommender for BO
- Precipitation flag uses multi-signal logic instead of only OD[0]
- Composite score available for ranking and BO target selection
- Extra audit outputs for model and design traceability
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import linregress, norm, qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.preprocessing import StandardScaler

# BayBE for Bayesian optimization (rounds 2+); fallback to GP if BayBE unavailable
import os as _os
if _os.environ.get("USE_BAYBE", "1") == "0":
    USE_BAYBE = False
else:
    try:
        from baybe import Campaign
        from baybe.objectives import SingleTargetObjective
        from baybe.parameters import NumericalContinuousParameter, CategoricalParameter
        from baybe.recommenders import RandomRecommender, TwoPhaseMetaRecommender
        try:
            from baybe.recommenders import BotorchRecommender
        except ImportError:
            from baybe.recommenders.pure.bayesian import SequentialGreedyRecommender as BotorchRecommender
        from baybe.searchspace import SearchSpace
        from baybe.targets import NumericalTarget
        USE_BAYBE = True
    except (ImportError, OSError, Exception):
        USE_BAYBE = False


# ============================================================
# 1. CONFIGURATION
# ============================================================

RANDOM_SEED = 42
rng = np.random.default_rng(RANDOM_SEED)

TEAM_NAME = "YOUR_TEAM_NAME"
EXPERIMENT_PLATE = f"{TEAM_NAME}_EXPERIMENT"
REAGENT_PLATE = f"{TEAM_NAME}_REAGENTS"
CELL_STOCK_PLATE = f"{TEAM_NAME}_CELLS"

# ── Volumes (uL) ──────────────────────────────────────────────────────────────
FINAL_WELL_VOLUME_UL = 200.0
CELL_VOLUME_UL = 20.0
MEDIA_TARGET_VOLUME_UL = FINAL_WELL_VOLUME_UL - CELL_VOLUME_UL

# Hardware-constrained pipetting range
MIN_TRANSFER_UL = 10.0
MAX_TRANSFER_UL = 200.0
MAX_REAGENT_VOLUME_UL = 200.0

# ── Well layout ───────────────────────────────────────────────────────────────
INTERIOR_WELLS = [
    f"{r}{c}"
    for c in range(2, 12)
    for r in list("BCDEFG")
]

CONTROL_SPREAD_ORDER = [
    "B2", "G11", "B11", "G2", "D6", "E7", "C4", "F9", "C9", "F4",
    "B6", "G7", "D10", "E3", "C2", "F11", "B8", "G5", "D4", "E9",
    "C6", "F7", "C11", "F2", "B4", "G9", "D2", "E11", "C8", "F5",
    "B10", "G3", "D8", "E5", "C3", "F10", "B5", "G8", "D11", "E2",
    "C7", "F6", "B3", "G10", "D5", "E8", "C10", "F3", "B7", "G4",
    "D3", "E10", "C5", "F8", "B9", "G6", "D7", "E4",
]

ROUND_WELL_BUDGET: Dict[int, int] = {
    1: 8,
    2: 8,
    3: 8,
    4: 8,
    5: 8,
}
DEFAULT_WELL_BUDGET = 8

ROUND_COMPOSITION: Dict[int, Dict[str, int]] = {
    1: dict(
        n_lhs=2,
        n_media_panel=2,
        n_ph_grad=0,
        n_nacl_grad=0,
        n_carbon_grad=0,
        n_bo=0,
        n_repeat=0,
        n_center=2,
        n_baseline=1,
        n_blanks=1,
    ),
    2: dict(
        n_lhs=0,
        n_media_panel=0,
        n_ph_grad=0,
        n_nacl_grad=0,
        n_carbon_grad=0,
        n_bo=4,
        n_repeat=1,
        n_center=1,
        n_baseline=1,
        n_blanks=1,
    ),
    3: dict(
        n_lhs=0,
        n_media_panel=0,
        n_ph_grad=0,
        n_nacl_grad=0,
        n_carbon_grad=0,
        n_bo=5,
        n_repeat=1,
        n_center=1,
        n_baseline=0,
        n_blanks=1,
    ),
}
DEFAULT_COMPOSITION = ROUND_COMPOSITION[2]

# ---------------------------------------------------------------------------
# Phase-2 optimization setup
# Optimized volumes (uL) for liquid components
# ---------------------------------------------------------------------------
NUMERIC_FACTORS = ["base_media_vol", "yeast_extract", "tryptone", "mops", "na_l_glut", "kh2po4", "glucose"]
OPTIMIZED_FACTOR_CONFIG: Dict[str, Tuple[float, float]] = {f: (0.0, MAX_TRANSFER_UL) for f in NUMERIC_FACTORS}

try:
    _media_df = pd.read_csv("reagents/base_media_set.csv")
    BASE_MEDIA_OPTIONS = _media_df["media_name"].dropna().tolist()
except Exception:
    BASE_MEDIA_OPTIONS = ["Novel Bio NBxCyclone Media"]

FACTOR_NAMES = ["base_media"] + NUMERIC_FACTORS
ALL_FACTOR_NAMES = FACTOR_NAMES + ["water"]

CONSTANTS: Dict[str, float] = {}
FACTOR_CONFIG = OPTIMIZED_FACTOR_CONFIG

BASELINE_CONDITION = {
    "base_media": BASE_MEDIA_OPTIONS[0],
    "base_media_vol": 0.0,
    "yeast_extract": 0.0,
    "tryptone": 0.0,
    "mops": 0.0,
    "na_l_glut": 0.0,
    "kh2po4": 0.0,
    "glucose": 0.0,
}
CENTER_POINT = {
    "base_media": BASE_MEDIA_OPTIONS[0],
    **{f: 20.0 for f in NUMERIC_FACTORS}
}

SIMULATION_MODE = False


# ============================================================
# 2. DATA STRUCTURES
# ============================================================

@dataclass
class WellDesign:
    well: str
    condition_type: str
    composition: Dict[str, float]
    source_note: str = ""


@dataclass
class WellResult:
    iteration: int
    well: str
    condition_type: str
    composition: Dict[str, float]
    mu_max_per_hr: float
    doubling_time_hr: Optional[float]
    auc: float
    endpoint_od: float
    od_readings: List[float]
    precipitation_flag: bool = False


def merge_with_constants(partial: Dict[str, float]) -> Dict[str, float]:
    full = {**CONSTANTS}
    full.update(partial)
    return full


def optimized_view(full: Dict[str, float]) -> Dict[str, float]:
    d = {f: float(full[f]) for f in NUMERIC_FACTORS}
    d["base_media"] = str(full["base_media"])
    return d





# ============================================================
# 3. GROWTH METRICS
# ============================================================

def compute_mu_max(time_hours: np.ndarray, od: np.ndarray, od_min: float = 0.03, window: int = 4) -> float:
    time_hours = np.asarray(time_hours, dtype=float)
    od = np.asarray(od, dtype=float)
    mask = np.isfinite(time_hours) & np.isfinite(od) & (od > od_min)
    time_hours = time_hours[mask]
    od = od[mask]

    if len(time_hours) < window + 1:
        return float("nan")

    log_od = np.log(od)
    slopes = []
    for i in range(len(time_hours) - window + 1):
        t_window = time_hours[i:i + window]
        y_window = log_od[i:i + window]
        if np.any(~np.isfinite(y_window)):
            continue
        slope, _, r_value, _, _ = linregress(t_window, y_window)
        if slope > 0 and (r_value ** 2) > 0.85:
            slopes.append(slope)

    return float(np.max(slopes)) if slopes else float("nan")


def compute_auc(time_hours: np.ndarray, od: np.ndarray) -> float:
    time_hours = np.asarray(time_hours, dtype=float)
    od = np.asarray(od, dtype=float)
    mask = np.isfinite(time_hours) & np.isfinite(od)
    if mask.sum() < 2:
        return float("nan")
    try:
        return float(np.trapezoid(od[mask], time_hours[mask]))
    except AttributeError:
        return float(np.trapz(od[mask], time_hours[mask]))


def compute_well_metrics(time_hours: np.ndarray, od: np.ndarray) -> Dict[str, float]:
    mu_max = compute_mu_max(time_hours, od)
    doubling_time = float(np.log(2) / mu_max) if np.isfinite(mu_max) and mu_max > 0 else float("nan")
    auc = compute_auc(time_hours, od)
    valid_od = od[np.isfinite(od)]
    endpoint = float(valid_od[-1]) if len(valid_od) > 0 else float("nan")
    return {
        "mu_max_per_hr": mu_max,
        "doubling_time_hr": doubling_time,
        "auc": auc,
        "endpoint_od": endpoint,
    }


def compute_composite_score(mu_max_per_hr: float, endpoint_od: float, auc: float, precipitation_flag: bool = False) -> float:
    values = {
        "mu_max_per_hr": mu_max_per_hr,
        "endpoint_od": endpoint_od,
        "auc": auc,
    }
    # Normalize to avoid AUC dominating the score simply due to scale.
    normalized = {
        "mu_max_per_hr": values["mu_max_per_hr"],
        "endpoint_od": values["endpoint_od"],
        "auc": values["auc"] / 2.0 if np.isfinite(values["auc"]) else float("nan"),
    }
    parts = []
    weights = []
    for metric, weight in COMPOSITE_WEIGHTS.items():
        value = normalized[metric]
        if np.isfinite(value):
            parts.append(weight * float(value))
            weights.append(weight)
    if not weights:
        score = float("nan")
    else:
        score = sum(parts) / sum(weights)
    if precipitation_flag and np.isfinite(score):
        score -= PRECIPITATION_SCORE_PENALTY
    return float(score)


# ============================================================
# 5. DESIGN CONSTRAINTS
# ============================================================

def _enforce_volume_constraint(c: Dict[str, float]) -> Dict[str, float]:
    num_sum = sum(c.get(f, 0.0) for f in NUMERIC_FACTORS)
    if num_sum > MAX_REAGENT_VOLUME_UL:
        scale = MAX_REAGENT_VOLUME_UL / num_sum
        for f in NUMERIC_FACTORS:
            c[f] = round(c.get(f, 0.0) * scale, 4)
    return c

def is_valid_condition(c: Dict[str, float]) -> bool:
    num_sum = sum(c.get(f, 0.0) for f in NUMERIC_FACTORS)
    if num_sum > MAX_REAGENT_VOLUME_UL + 0.1: # allow slight floating point
        return False
    for f in NUMERIC_FACTORS:
        val = c.get(f, 0.0)
        lo, hi = FACTOR_CONFIG[f]
        if val < lo - 0.1 or val > hi + 0.1:
            return False
    if "base_media" in c and c["base_media"] not in BASE_MEDIA_OPTIONS:
        return False
    return True


# ============================================================
# 6. FACTOR SCALING
# ============================================================

def vector_to_condition(x: np.ndarray) -> Dict[str, float]:
    c = {f: float(v) for f, v in zip(NUMERIC_FACTORS, x)}
    c["base_media"] = rng.choice(BASE_MEDIA_OPTIONS)
    return c


def unique_conditions(conditions: List[Dict[str, float]], decimals: int = 4) -> List[Dict[str, float]]:
    seen = set()
    unique = []
    for c in conditions:
        key = tuple([round(c[f], decimals) for f in NUMERIC_FACTORS] + [c["base_media"]])
        if key not in seen:
            seen.add(key)
            unique.append(optimized_view(merge_with_constants(c)))
    return unique


# ============================================================
# 7. SAMPLING HELPERS
# ============================================================

def _sample_random_conditions(n: int) -> List[Dict[str, float]]:
    conds = []
    for _ in range(n):
        c = {
            factor: float(rng.uniform(lo, hi))
            for factor, (lo, hi) in FACTOR_CONFIG.items()
        }
        c["base_media"] = rng.choice(BASE_MEDIA_OPTIONS)
        conds.append(c)
    return conds


def _sobol_sample_conditions(n_points: int, oversample_factor: int = 4) -> List[Dict[str, float]]:
    n_dim = len(NUMERIC_FACTORS)
    m = math.ceil(math.log2(max(8, n_points * oversample_factor)))
    sampler = qmc.Sobol(d=n_dim, scramble=True, seed=RANDOM_SEED)
    raw = sampler.random_base2(m=m)
    bounds_low = np.array([FACTOR_CONFIG[f][0] for f in NUMERIC_FACTORS])
    bounds_high = np.array([FACTOR_CONFIG[f][1] for f in NUMERIC_FACTORS])
    scaled = qmc.scale(raw, bounds_low, bounds_high)

    conditions = []
    for row in scaled:
        c = vector_to_condition(row)
        c = _enforce_volume_constraint(c)
        if is_valid_condition(c):
            conditions.append(c)
        if len(conditions) >= n_points:
            break
    return unique_conditions(conditions)


def latin_hypercube_sample(n_points: int) -> List[Dict[str, float]]:
    sampler = qmc.LatinHypercube(d=len(NUMERIC_FACTORS), seed=RANDOM_SEED)
    raw_samples = sampler.random(n=n_points * 3)
    bounds_low = np.array([FACTOR_CONFIG[f][0] for f in NUMERIC_FACTORS])
    bounds_high = np.array([FACTOR_CONFIG[f][1] for f in NUMERIC_FACTORS])
    scaled = qmc.scale(raw_samples, bounds_low, bounds_high)

    conditions = []
    for row in scaled:
        c = vector_to_condition(row)
        c = _enforce_volume_constraint(c)
        if is_valid_condition(c):
            conditions.append(c)
        if len(conditions) >= n_points:
            break

    if len(conditions) < n_points:
        extras = [c for c in _sample_random_conditions(500) if is_valid_condition(c)]
        conditions.extend(extras[: n_points - len(conditions)])

    return unique_conditions(conditions)[:n_points]


# Gradient functions removed


# ============================================================
# 8. BayBE / GP FALLBACK — BATCH PROPOSAL (BO rounds 2+)
# ============================================================

BAYBE_TARGET_NAME = "score"


# Scaler is now built dynamically to avoid staleness if FACTOR_CONFIG changes


def condition_to_vector(c: Dict[str, float]) -> np.ndarray:
    return np.array([c[f] for f in NUMERIC_FACTORS], dtype=float)


def _build_gp(alpha: float | np.ndarray = 1e-6) -> GaussianProcessRegressor:
    n_factors = len(NUMERIC_FACTORS)
    kernel = (
        ConstantKernel(1.0, constant_value_bounds=(1e-3, 1e3))
        * Matern(length_scale=np.ones(n_factors), nu=2.5)
    )
    return GaussianProcessRegressor(
        kernel=kernel,
        alpha=alpha,
        normalize_y=True,
        n_restarts_optimizer=8,
        random_state=RANDOM_SEED,
    )


def _gp_propose_batch(
    aggregated: pd.DataFrame,
    n_candidates: int,
    xi: float = 0.01,
) -> List[Dict[str, float]]:
    X_raw = aggregated[NUMERIC_FACTORS].values.astype(float)
    y = aggregated["target_mean"].values.astype(float)
    
    corners = np.array([
        [lo for lo, _ in FACTOR_CONFIG.values()],
        [hi for _, hi in FACTOR_CONFIG.values()],
    ])
    scaler = StandardScaler()
    scaler.fit(corners)
    
    X_hist_scaled = scaler.transform(X_raw)
    replicate_count = aggregated["replicate_count"].astype(float).clip(lower=1.0).to_numpy()
    target_std = aggregated["target_std"].astype(float).fillna(0.05).clip(lower=0.02).to_numpy()
    per_point_alpha = np.maximum((target_std ** 2) / replicate_count, 1e-6)
    model = _build_gp(alpha=per_point_alpha)
    model.fit(X_hist_scaled, y)

    pool = _sobol_sample_conditions(4096)
    if len(pool) < 512:
        fallback = [c for c in _sample_random_conditions(5000) if is_valid_condition(c)]
        pool.extend(fallback)
    pool = unique_conditions(pool)
    if not pool:
        return latin_hypercube_sample(n_candidates)

    X_pool_raw = np.vstack([condition_to_vector(c) for c in pool])
    X_pool_scaled = scaler.transform(X_pool_raw)
    y_best = float(np.nanmax(y))
    mu, sigma = model.predict(X_pool_scaled, return_std=True)
    sigma = np.maximum(sigma, 1e-9)
    improvement = mu - y_best - xi
    z = improvement / sigma
    ei = improvement * norm.cdf(z) + sigma * norm.pdf(z)
    ei[sigma <= 1e-9] = 0.0
    ranked_indices = np.argsort(ei)[::-1]
    selected: List[Dict[str, float]] = []
    selected_scaled: List[np.ndarray] = []
    min_sep = 0.35
    for idx in ranked_indices:
        c = pool[idx]
        x_sc = X_pool_scaled[idx]
        if any(np.linalg.norm(x_sc - h) < 1e-6 for h in X_hist_scaled):
            continue
        if any(np.linalg.norm(x_sc - s) < min_sep for s in selected_scaled):
            continue
        selected.append(c)
        selected_scaled.append(x_sc)
        if len(selected) >= n_candidates:
            break
    if len(selected) < n_candidates:
        for idx in ranked_indices:
            c = pool[idx]
            x_sc = X_pool_scaled[idx]
            if any(np.allclose(x_sc, s, atol=1e-4) for s in selected_scaled):
                continue
            selected.append(c)
            selected_scaled.append(x_sc)
            if len(selected) >= n_candidates:
                break
    return selected[:n_candidates]


def _build_baybe_searchspace() -> SearchSpace:
    parameters = [
        NumericalContinuousParameter(name=f, bounds=FACTOR_CONFIG[f])
        for f in NUMERIC_FACTORS
    ]
    parameters.append(CategoricalParameter(name="base_media", values=BASE_MEDIA_OPTIONS))
    return SearchSpace.from_product(parameters)


def _build_baybe_campaign() -> Campaign:
    searchspace = _build_baybe_searchspace()
    target = NumericalTarget(name=BAYBE_TARGET_NAME, mode="MAX")
    objective = SingleTargetObjective(target)
    recommender = TwoPhaseMetaRecommender(
        initial_recommender=RandomRecommender(),
        recommender=BotorchRecommender(),
        switch_after=1,
    )
    return Campaign(
        searchspace=searchspace,
        objective=objective,
        recommender=recommender,
    )


def get_xi(iteration: int, total_iterations: int) -> float:
    max_xi, min_xi = 0.10, 0.01
    if total_iterations <= 1:
        return max_xi
    progress = (iteration - 1) / (total_iterations - 1)
    return round(max_xi - (max_xi - min_xi) * progress, 4)


def baybe_propose_batch(history_df: pd.DataFrame, n_candidates: int, xi: float = 0.01) -> List[Dict[str, float]]:
    aggregated = aggregate_history_for_model(history_df)
    if len(aggregated) < 4:
        print(f"  [BO] Only {len(aggregated)} clean unique conditions — falling back to LHS.")
        return latin_hypercube_sample(n_candidates)

    if not USE_BAYBE:
        print(f"  [GP] Recommending {n_candidates} conditions (BayBE not installed, using GP fallback).")
        return _gp_propose_batch(aggregated, n_candidates, xi=xi)

    campaign = _build_baybe_campaign()
    measurements = aggregated[FACTOR_NAMES + ["target_mean"]].copy()
    measurements = measurements.rename(columns={"target_mean": BAYBE_TARGET_NAME})
    campaign.add_measurements(measurements)

    rec = campaign.recommend(batch_size=n_candidates * 2)
    conditions: List[Dict[str, float]] = []
    for _, row in rec.iterrows():
        c = {f: round(float(row[f]), 4) for f in NUMERIC_FACTORS}
        c["base_media"] = str(row["base_media"])
        c = _enforce_volume_constraint(c)
        if is_valid_condition(c):
            conditions.append(optimized_view(merge_with_constants(c)))
        if len(conditions) >= n_candidates:
            break

    if len(conditions) < n_candidates:
        print(f"  [BayBE] {len(conditions)} valid after filtering — filling with LHS.")
        conditions.extend(latin_hypercube_sample(n_candidates * 10))
    conditions = unique_conditions(conditions)[:n_candidates]
    print(f"  [BayBE] Recommended {len(conditions)} conditions from {len(aggregated)} training points.")
    return conditions


# ============================================================
# 10. TRANSFER CALCULATIONS
# ============================================================

def calc_transfer_ul(final_conc: float, stock_conc: float, final_volume_ul: float = FINAL_WELL_VOLUME_UL) -> float:
    return (final_conc * final_volume_ul) / stock_conc


def calculate_well_volumes(composition: Dict[str, float], condition_type: str) -> Dict[str, float]:
    """Calculate the required volume of each stock solution to achieve the target composition."""
    volumes = {}
    if condition_type == "blank":
        return volumes
        
    full = merge_with_constants(composition)
    for factor in ALL_FACTOR_NAMES:
        if factor == "pH":
            continue
        final_conc = full[factor]
        stock_info = STOCKS[factor]
        vol = calc_transfer_ul(final_conc, stock_info["stock_conc"])
        if vol >= MIN_TRANSFER_UL:
            volumes[factor] = vol
            
    return volumes

def composition_to_transfers(dst_well: str, composition: Dict[str, float], condition_type: str) -> List[Dict]:
    full = merge_with_constants(composition)
    transfers: List[Dict] = []
    
    target_ph = full.get("pH", BASE_PH)
    ph_reagent, ph_vol_ul = ph_adjustment_volume(target_ph, BASE_PH)
    
    volumes = calculate_well_volumes(composition, condition_type)
    nutrient_vol = sum(volumes.values())

    for factor, vol in volumes.items():
        if vol > MAX_TRANSFER_UL:
            raise ValueError(
                f"Transfer too large: {factor} → {dst_well} = {vol:.2f} uL (max {MAX_TRANSFER_UL} uL)."
            )
        stock_info = STOCKS[factor]
        transfers.append({
            "src_plate": "reagent",
            "src_well": stock_info["src_well"],
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": round(vol, 2),
            "new_tip": "once",
            "blow_out": True,
            "step": "A_nutrients",
        })

    media_fill = MEDIA_TARGET_VOLUME_UL - nutrient_vol - ph_vol_ul
    if media_fill < -1e-6:
        raise ValueError(
            f"Negative base media fill for {dst_well}: nutrients={nutrient_vol:.1f} uL + pH_adj={ph_vol_ul:.1f} uL > {MEDIA_TARGET_VOLUME_UL:.1f} uL"
        )

    if media_fill >= MIN_TRANSFER_UL:
        transfers.append({
            "src_plate": "reagent",
            "src_well": STOCKS["BaseMedia"]["src_well"],
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": round(media_fill, 2),
            "new_tip": "once",
            "blow_out": True,
            "step": "A_base_media_fill",
        })

    if condition_type != "blank" and ph_reagent != "none":
        transfers.append({
            "src_plate": "reagent",
            "src_well": STOCKS[ph_reagent]["src_well"],
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": round(ph_vol_ul, 2),
            "new_tip": "once",
            "blow_out": True,
            "step": "B_pH_adjust",
            "comment": f"Target pH {full.get('pH', BASE_PH):.2f} — adding {ph_reagent} {ph_vol_ul:.1f} uL",
        })

    if condition_type != "blank":
        transfers.append({
            "src_plate": "cell_culture_stock",
            "src_well": CELL_SOURCE_WELL,
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": round(CELL_VOLUME_UL, 2),
            "new_tip": "always",
            "blow_out": False,
            "post_mix_volume": 40,
            "post_mix_reps": 3,
            "step": "C_seed_cells",
        })

    return transfers


def validate_transfers(transfers: List[Dict]) -> None:
    valid_src_plates = {"reagent", "cell_culture_stock", "experiment"}
    for i, t in enumerate(transfers):
        if t["src_plate"] not in valid_src_plates:
            raise ValueError(f"Transfer {i}: invalid src_plate '{t['src_plate']}'.")
        vol = t.get("volume", 0)
        
        # pH adjustments are allowed to be small (bypass MIN_TRANSFER_UL)
        if t.get("step") == "B_pH_adjust":
            if not (0 < vol <= 1000):
                raise ValueError(f"Transfer {i}: pH adjustment volume {vol:.2f} uL is out of range (0, 1000].")
        else:
            if not (MIN_TRANSFER_UL <= vol <= 1000):
                raise ValueError(f"Transfer {i}: volume {vol:.2f} uL is out of range [{MIN_TRANSFER_UL}, 1000].")


# ============================================================
# 11. PLATE DESIGN
# ============================================================

def select_best_unique_conditions(results_df: pd.DataFrame, n: int) -> List[Dict[str, float]]:
    if results_df.empty:
        return []
    score_col = "target_mean" if "target_mean" in results_df.columns else "mu_max_per_hr"
    grouped = (
        results_df
        .groupby(FACTOR_NAMES, dropna=False)[score_col]
        .median()
        .reset_index()
        .sort_values(score_col, ascending=False)
    )
    return grouped.head(n)[FACTOR_NAMES].to_dict(orient="records")


def _split_controls_and_experiments(designs: List[WellDesign]) -> Tuple[List[WellDesign], List[WellDesign]]:
    control_types = {"baseline", "center", "blank"}
    controls = [d for d in designs if d.condition_type in control_types]
    experiments = [d for d in designs if d.condition_type not in control_types]
    return controls, experiments


def _assign_wells_with_spread(designs: List[WellDesign], wells: List[str]) -> List[WellDesign]:
    controls, experiments = _split_controls_and_experiments(designs)
    
    # We use python's random.Random for this specific shuffling to keep it deterministic with seed
    local_rng = random.Random(RANDOM_SEED + len(designs))
    local_rng.shuffle(controls)
    local_rng.shuffle(experiments)

    assigned_wells: Dict[int, str] = {}
    available_wells = list(wells)

    spread_wells = [w for w in CONTROL_SPREAD_ORDER if w in available_wells]
    for design, well in zip(controls, spread_wells):
        design.well = well
        assigned_wells[id(design)] = well
        available_wells.remove(well)

    rng.shuffle(available_wells)
    for design in experiments:
        if not available_wells:
            raise ValueError("Ran out of wells while assigning experiments.")
        design.well = available_wells.pop()
        assigned_wells[id(design)] = design.well

    for design in controls[len(spread_wells):]:
        if not available_wells:
            raise ValueError("Ran out of wells while assigning controls.")
        design.well = available_wells.pop()
        assigned_wells[id(design)] = design.well

    return designs


def build_plate_design(
    iteration: int,
    total_iterations: int,
    history_df: pd.DataFrame,
) -> List[WellDesign]:
    comp = ROUND_COMPOSITION.get(iteration, DEFAULT_COMPOSITION)
    budget = ROUND_WELL_BUDGET.get(iteration, DEFAULT_WELL_BUDGET)
    wells = INTERIOR_WELLS[:budget]
    designs: List[WellDesign] = []

    if comp["n_lhs"] > 0:
        lhs_conditions = latin_hypercube_sample(comp["n_lhs"])
        for c in lhs_conditions:
            designs.append(WellDesign(well="", condition_type="lhs", composition=c, source_note="lhs_round1"))

    if comp["n_media_panel"] > 0:
        for c in MANUAL_MEDIA_PANEL[: comp["n_media_panel"]]:
            designs.append(WellDesign(well="", condition_type="media_panel", composition=c, source_note="manual_media_panel"))

    if comp["n_bo"] > 0:
        if history_df.empty:
            bo_conditions = latin_hypercube_sample(comp["n_bo"])
            source = "lhs_fallback"
        else:
            xi = get_xi(iteration, total_iterations)
            bo_conditions = baybe_propose_batch(history_df, comp["n_bo"], xi=xi)
            source = f"baybe_iter{iteration}" if USE_BAYBE else f"gp_iter{iteration}"
        for c in bo_conditions:
            designs.append(WellDesign(well="", condition_type="candidate", composition=c, source_note=source))

    if comp["n_repeat"] > 0:
        best_conditions = select_best_unique_conditions(history_df, max(1, min(4, comp["n_repeat"])))
        if not best_conditions:
            best_conditions = [BASELINE_CONDITION]
        repeat_pool: List[Dict[str, float]] = []
        while len(repeat_pool) < comp["n_repeat"]:
            repeat_pool.extend(best_conditions)
        for c in repeat_pool[: comp["n_repeat"]]:
            designs.append(WellDesign(well="", condition_type="repeat_best", composition=c, source_note="top_previous_condition"))

    for _ in range(comp["n_center"]):
        designs.append(WellDesign(well="", condition_type="center", composition=CENTER_POINT.copy(), source_note="center_point"))

    for _ in range(comp["n_baseline"]):
        designs.append(WellDesign(well="", condition_type="baseline", composition=BASELINE_CONDITION.copy(), source_note="baseline_control"))

    blank_composition = {f: 0.0 for f in FACTOR_NAMES}
    for _ in range(comp["n_blanks"]):
        designs.append(WellDesign(well="", condition_type="blank", composition=blank_composition.copy(), source_note="blank_no_cells"))

    if len(designs) > len(wells):
        raise ValueError(f"Round {iteration}: {len(designs)} designs exceed {len(wells)} available wells.")

    return _assign_wells_with_spread(designs, wells)


def build_transfer_array_from_design(designs: List[WellDesign]) -> List[Dict]:
    transfers: List[Dict] = []
    for d in designs:
        transfers.extend(composition_to_transfers(d.well, d.composition, d.condition_type))
    validate_transfers(transfers)
    return transfers


# ============================================================
# 12. MULTI-PLATE DATA INGESTION
# ============================================================

import glob

def load_historical_plate_data(data_dir: str = "data") -> pd.DataFrame:
    all_rows = []
    plate_reps = glob.glob(f"{data_dir}/*_replicates.csv")
    for rep_file in plate_reps:
        prefix = rep_file.replace("_replicates.csv", "")
        growth_file = f"{prefix}_growth.csv"
        map_file = f"{prefix}_plate_condition_map.csv"
        
        if not (Path(growth_file).exists() and Path(map_file).exists()):
            continue
            
        reps_df = pd.read_csv(rep_file)
        growth_df = pd.read_csv(growth_file)
        map_df = pd.read_csv(map_file)
        
        merged1 = reps_df.merge(growth_df[["condition_id", "well"]].drop_duplicates(), on="condition_id", how="inner")
        merged2 = merged1.merge(map_df, on="well", how="inner")
        
        for _, row in merged2.iterrows():
            c = {
                "base_media": row["base_media"],
                "target_mean": float(row["mean_growth_rate_per_hr"]),
                "replicate_count": float(row.get("n_replicates", 1.0)),
            }
            if "variance_growth_rate_per_hr" in row and pd.notna(row["variance_growth_rate_per_hr"]):
                c["target_std"] = max(0.01, float(row["variance_growth_rate_per_hr"])**0.5)
            else:
                c["target_std"] = 0.05
                
            for f in NUMERIC_FACTORS:
                c[f] = float(row.get(f, 0.0))
            
            c["condition_type"] = "historical"
            all_rows.append(c)
            
    df = pd.DataFrame(all_rows)
    if not df.empty:
        agg_cols = {"target_mean": "mean", "replicate_count": "sum", "target_std": "mean"}
        df = df.groupby(FACTOR_NAMES, dropna=False).agg(agg_cols).reset_index()
        # Drop entries where growth might be 0 or broken if we wanted, but we trust the input
    return df

def aggregate_history_for_model(history_df: pd.DataFrame) -> pd.DataFrame:
    # History DF is already aggregated by load_historical_plate_data
    return history_df

# ============================================================
# 13. PREDICTIONS & OUTPUT
# ============================================================

def predict_growth_rates(aggregated_df: pd.DataFrame, conditions: List[Dict[str, float]]) -> List[float]:
    X_hist_raw = aggregated_df[NUMERIC_FACTORS].values.astype(float)
    y_hist = aggregated_df["target_mean"].values.astype(float)
    
    corners = np.array([
        [lo for lo, _ in FACTOR_CONFIG.values()],
        [hi for _, hi in FACTOR_CONFIG.values()],
    ])
    scaler = StandardScaler()
    scaler.fit(corners)
    
    X_hist_scaled = scaler.transform(X_hist_raw)
    replicate_count = aggregated_df["replicate_count"].astype(float).clip(lower=1.0).to_numpy()
    target_std = aggregated_df["target_std"].astype(float).fillna(0.05).clip(lower=0.02).to_numpy()
    per_point_alpha = np.maximum((target_std ** 2) / replicate_count, 1e-6)
    
    model = _build_gp(alpha=per_point_alpha)
    model.fit(X_hist_scaled, y_hist)
    
    X_pool_raw = np.vstack([condition_to_vector(c) for c in conditions])
    X_pool_scaled = scaler.transform(X_pool_raw)
    mu_pred, _ = model.predict(X_pool_scaled, return_std=True)
    return [float(m) for m in mu_pred]

def save_next_round_plate_map(designs: List[WellDesign], predicted_rates: List[float], out_csv: Path) -> None:
    rows = []
    for d, pred_rate in zip(designs, predicted_rates):
        c = d.composition.copy()
        num_sum = sum(c.get(f, 0.0) for f in NUMERIC_FACTORS)
        water_vol = max(0.0, MAX_REAGENT_VOLUME_UL - num_sum)
        
        row = {
            "well": d.well,
            "condition": f"BO_Round_{d.condition_type}",
            "base_media": c["base_media"]
        }
        for f in NUMERIC_FACTORS:
            row[f] = round(c.get(f, 0.0), 1)
        row["water"] = round(water_vol, 1)
        row["cells"] = round(CELL_VOLUME_UL, 1)
        row["total"] = round(num_sum + water_vol + CELL_VOLUME_UL, 1)
        row["predicted_growth_rate_per_hr"] = round(pred_rate, 4)
        
        rows.append(row)
        
    pd.DataFrame(rows).to_csv(out_csv, index=False)

# ============================================================
# 14. MAIN LOOP
# ============================================================

def run_closed_loop(output_dir: str = "bo_outputs") -> None:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("Closed-Loop Bayesian Optimization Agent (Multi-Plate Input Edition)")
    print("Optimizer       : BayBE" if USE_BAYBE else "Optimizer       : GP (BayBE not installed)")
    print(f"Target variable : mean_growth_rate_per_hr")
    print(f"Categorical var : base_media")
    print(f"Numerical vars  : {NUMERIC_FACTORS}")
    print("=" * 72)

    print("Loading historical data...")
    history_df = load_historical_plate_data("data")
    if history_df.empty:
        print("No historical data found! Providing LHS initial design.")
    else:
        print(f"Loaded {len(history_df)} unique historical conditions from plates.")
        
    print("Generating 20 BO proposals...")
    n_proposals = 20
    designs: List[WellDesign] = []
    
    if history_df.empty:
        # Fallback to pure random LHS if no history
        bo_conditions = latin_hypercube_sample(n_proposals)
        source = "lhs_fallback"
    else:
        # Request 20 candidates from BayBE/GP
        bo_conditions = baybe_propose_batch(history_df, n_proposals, xi=0.01)
        source = "baybe" if USE_BAYBE else "gp_fallback"
        
    for i, c in enumerate(bo_conditions):
        well_id = f"P{i+1}" # arbitrary well IDs for proposals
        designs.append(WellDesign(well=well_id, condition_type="candidate", composition=c, source_note=source))

    if not history_df.empty:
        predicted_rates = predict_growth_rates(history_df, [d.composition for d in designs])
    else:
        predicted_rates = [0.0 for _ in designs]
        
    # Sort designs and predicted_rates by predicted_rates descending
    sorted_pairs = sorted(zip(designs, predicted_rates), key=lambda x: x[1], reverse=True)
    designs = [pair[0] for pair in sorted_pairs]
    predicted_rates = [pair[1] for pair in sorted_pairs]
    
    # re-assign ranks to 'well' or condition name
    for i, d in enumerate(designs):
        d.well = f"Rank_{i+1}"

    out_csv = outdir / "next_round_plate_condition_map.csv"
    save_next_round_plate_map(designs, predicted_rates, out_csv)

    print(f"\nSaved next round plate map with predictions: {out_csv}")
    print(f"{'=' * 72}")

if __name__ == "__main__":
    run_closed_loop()
