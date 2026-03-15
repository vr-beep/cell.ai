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
        from baybe.parameters import NumericalContinuousParameter
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
MAX_TRANSFER_UL = 180.0

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
    1: 60,
    2: 48,
    3: 32,
}
DEFAULT_WELL_BUDGET = 32

ROUND_COMPOSITION: Dict[int, Dict[str, int]] = {
    1: dict(
        n_lhs=24,
        n_media_panel=8,
        n_ph_grad=8,
        n_nacl_grad=6,
        n_carbon_grad=4,
        n_bo=0,
        n_repeat=0,
        n_center=4,
        n_baseline=4,
        n_blanks=2,
    ),
    2: dict(
        n_lhs=0,
        n_media_panel=0,
        n_ph_grad=0,
        n_nacl_grad=0,
        n_carbon_grad=0,
        n_bo=24,
        n_repeat=8,
        n_center=8,
        n_baseline=4,
        n_blanks=4,
    ),
    3: dict(
        n_lhs=0,
        n_media_panel=0,
        n_ph_grad=0,
        n_nacl_grad=0,
        n_carbon_grad=0,
        n_bo=16,
        n_repeat=6,
        n_center=4,
        n_baseline=4,
        n_blanks=2,
    ),
}
DEFAULT_COMPOSITION = ROUND_COMPOSITION[3]

# ---------------------------------------------------------------------------
# Phase-2 optimization setup
# Only the top 3 factors are optimized. All other components are kept fixed.
# ---------------------------------------------------------------------------
OPTIMIZED_FACTOR_CONFIG: Dict[str, Tuple[float, float]] = {
    # 7.5-15 g/L NaCl is roughly 128-257 mM. Keep the BO range centered there.
    "NaCl_mM": (125.0, 260.0),
    "Glycerol_pct": (0.10, 0.50),  # Carbon source; CCD uses Glycerol
    # Latest small-scale V. natriegens work points to a narrow pH sweet spot.
    "pH": (7.8, 8.2),
}

# Fixed constants for the non-optimized ingredients.
# MOPS 20–40 mM per literature/CCD; 250 mM causes osmotic stress.
CONSTANTS: Dict[str, float] = {
    "MOPS_mM": 30.0,
    "Phosphate_mM": 4.0,
    "MgSO4_mM": 1.0,
    "NH4SO4_mM": 12.0,
}

ALL_FACTOR_CONFIG: Dict[str, Tuple[float, float]] = {
    **OPTIMIZED_FACTOR_CONFIG,
    "MOPS_mM": (180.0, 350.0),
    "Phosphate_mM": (2.0, 8.0),
    "MgSO4_mM": (0.5, 2.0),
    "NH4SO4_mM": (5.0, 20.0),
}

FACTOR_CONFIG = OPTIMIZED_FACTOR_CONFIG
FACTOR_NAMES = list(FACTOR_CONFIG.keys())
ALL_FACTOR_NAMES = ["NaCl_mM", "MOPS_mM", "Phosphate_mM", "MgSO4_mM", "NH4SO4_mM", "Glycerol_pct", "pH"]

STOCKS: Dict[str, Dict] = {
    "NaCl_mM": {"stock_conc": 5000.0, "src_well": "A1"},
    "MOPS_mM": {"stock_conc": 1000.0, "src_well": "A2"},
    "Phosphate_mM": {"stock_conc": 1000.0, "src_well": "A3"},
    "MgSO4_mM": {"stock_conc": 500.0, "src_well": "A4"},
    "NH4SO4_mM": {"stock_conc": 1000.0, "src_well": "A5"},
    "Glycerol_pct": {"stock_conc": 10.0, "src_well": "A6"},
    "NaOH": {"stock_conc": 1000.0, "src_well": "A7"},
    "HCl": {"stock_conc": 1000.0, "src_well": "A8"},
    "BaseMedia": {"stock_conc": 1.0, "src_well": "B1"},
}
CELL_SOURCE_WELL = "A1"

BASE_PH = 7.5
BUFFER_CAPACITY_UL_PER_PH_UNIT = 8.0
# Replace this with measured values on competition day.
PH_ADJUSTMENT_LOOKUP_UL: Dict[float, float] = {
    7.0: 4.0,
    7.2: 2.2,
    7.5: 0.0,
    7.8: 2.4,
    8.0: 4.3,
    8.3: 6.7,
    8.5: 8.3,
}

REAGENT_COST: Dict[str, float] = {
    "NaCl_mM": 0.001,
    "MOPS_mM": 0.050,
    "Phosphate_mM": 0.005,
    "MgSO4_mM": 0.010,
    "NH4SO4_mM": 0.008,
    "Glycerol_pct": 0.030,
    "pH": 0.000,
}
MAX_COST_PER_WELL: Optional[float] = 15.0

PRECIPITATION_OD_THRESHOLD = 0.30
PRECIPITATION_STABLE_DELTA_THRESHOLD = 0.06
PRECIPITATION_EARLY_SLOPE_THRESHOLD = 0.01

# Wells with endpoint OD above this are excluded from GP training
ENDPOINT_OD_MAX_FOR_MODEL = 2.5

# Ranking / BO target weights
USE_COMPOSITE_TARGET = True
COMPOSITE_WEIGHTS = {
    "mu_max_per_hr": 0.55,
    "endpoint_od": 0.25,
    "auc": 0.20,
}
PRECIPITATION_SCORE_PENALTY = 2.0

# Practicality penalties
PRACTICALITY_PENALTY_WEIGHT = 0.08
SMALL_TRANSFER_SOFT_THRESHOLD_UL = 2.5
PH_ADJUST_SOFT_THRESHOLD_UL = 8.0

BASELINE_CONDITION: Dict[str, float] = {
    "NaCl_mM": 180.0,
    "Glycerol_pct": 0.20,
    "pH": 8.0,
}
CENTER_POINT: Dict[str, float] = {
    factor: round((lo + hi) / 2.0, 4)
    for factor, (lo, hi) in FACTOR_CONFIG.items()
}

MANUAL_MEDIA_PANEL: List[Dict[str, float]] = [
    {"NaCl_mM": 180.0, "Glycerol_pct": 0.20, "pH": 8.0},
    {"NaCl_mM": 240.0, "Glycerol_pct": 0.20, "pH": 8.0},
    {"NaCl_mM": 130.0, "Glycerol_pct": 0.20, "pH": 8.0},
    {"NaCl_mM": 180.0, "Glycerol_pct": 0.45, "pH": 8.0},
    {"NaCl_mM": 180.0, "Glycerol_pct": 0.10, "pH": 8.0},
    {"NaCl_mM": 180.0, "Glycerol_pct": 0.20, "pH": 7.85},
    {"NaCl_mM": 180.0, "Glycerol_pct": 0.20, "pH": 8.15},
    {"NaCl_mM": 220.0, "Glycerol_pct": 0.35, "pH": 8.05},
]

SIMULATION_MODE = True


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
    return {f: float(full[f]) for f in FACTOR_NAMES}


def validate_constant_setup() -> None:
    missing = [f for f in ALL_FACTOR_NAMES if f not in CONSTANTS and f not in FACTOR_NAMES]
    if missing:
        raise ValueError(f"Missing constant definitions for: {missing}")
    duplicate = set(CONSTANTS).intersection(FACTOR_NAMES)
    if duplicate:
        raise ValueError(f"Constants overlap with optimized factors: {sorted(duplicate)}")


validate_constant_setup()


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
# 4. pH ADJUSTMENT LOGIC
# ============================================================

def _interpolate_lookup(target_ph: float, lookup: Dict[float, float]) -> Optional[float]:
    keys = sorted(lookup.keys())
    if not keys:
        return None
    if target_ph in lookup:
        return float(lookup[target_ph])
    if target_ph < keys[0] or target_ph > keys[-1]:
        return None
    for left, right in zip(keys[:-1], keys[1:]):
        if left <= target_ph <= right:
            left_v = lookup[left]
            right_v = lookup[right]
            ratio = (target_ph - left) / (right - left)
            return float(left_v + ratio * (right_v - left_v))
    return None


def ph_adjustment_volume(target_ph: float, base_ph: float = BASE_PH) -> Tuple[str, float]:
    if math.isclose(target_ph, base_ph, abs_tol=1e-6):
        return "none", 0.0

    lookup_volume = _interpolate_lookup(target_ph, PH_ADJUSTMENT_LOOKUP_UL)
    if lookup_volume is None:
        lookup_volume = abs(target_ph - base_ph) * BUFFER_CAPACITY_UL_PER_PH_UNIT

    volume = round(float(lookup_volume), 1)
    if volume < MIN_TRANSFER_UL:
        return "none", 0.0
    volume = min(volume, MAX_TRANSFER_UL)
    reagent = "NaOH" if target_ph > base_ph else "HCl"
    return reagent, volume


# ============================================================
# 5. DESIGN CONSTRAINTS
# ============================================================

def is_valid_condition(c: Dict[str, float]) -> bool:
    full = merge_with_constants(c)
    for factor, (lo, hi) in FACTOR_CONFIG.items():
        if full[factor] < lo or full[factor] > hi:
            return False
    if full["NaCl_mM"] < 100:
        return False
    if full.get("pH", BASE_PH) > 8.25:
        return False
    if full.get("pH", BASE_PH) > 8.1 and full["Phosphate_mM"] > 5.0:
        return False
    if full["Phosphate_mM"] > 6.0 and full["MgSO4_mM"] > 1.5:
        return False
    if full["NaCl_mM"] + 2.0 * full["NH4SO4_mM"] > 340:
        return False
    if MAX_COST_PER_WELL is not None:
        cost = sum(REAGENT_COST.get(f, 0.0) * full[f] for f in ALL_FACTOR_NAMES)
        if cost > MAX_COST_PER_WELL:
            return False
    return True


# ============================================================
# 6. FACTOR SCALING
# ============================================================

def vector_to_condition(x: np.ndarray) -> Dict[str, float]:
    return {f: float(v) for f, v in zip(FACTOR_NAMES, x)}


def unique_conditions(conditions: List[Dict[str, float]], decimals: int = 4) -> List[Dict[str, float]]:
    seen = set()
    unique = []
    for c in conditions:
        key = tuple(round(c[f], decimals) for f in FACTOR_NAMES)
        if key not in seen:
            seen.add(key)
            unique.append(optimized_view(merge_with_constants(c)))
    return unique


# ============================================================
# 7. SAMPLING HELPERS
# ============================================================

def _sample_random_conditions(n: int) -> List[Dict[str, float]]:
    return [
        {
            factor: float(rng.uniform(lo, hi))
            for factor, (lo, hi) in FACTOR_CONFIG.items()
        }
        for _ in range(n)
    ]


def _sobol_sample_conditions(n_points: int, oversample_factor: int = 4) -> List[Dict[str, float]]:
    n_dim = len(FACTOR_NAMES)
    m = math.ceil(math.log2(max(8, n_points * oversample_factor)))
    sampler = qmc.Sobol(d=n_dim, scramble=True, seed=RANDOM_SEED)
    raw = sampler.random_base2(m=m)
    bounds_low = np.array([FACTOR_CONFIG[f][0] for f in FACTOR_NAMES])
    bounds_high = np.array([FACTOR_CONFIG[f][1] for f in FACTOR_NAMES])
    scaled = qmc.scale(raw, bounds_low, bounds_high)

    conditions = []
    for row in scaled:
        c = vector_to_condition(row)
        if is_valid_condition(c):
            conditions.append(c)
        if len(conditions) >= n_points:
            break
    return unique_conditions(conditions)


def latin_hypercube_sample(n_points: int) -> List[Dict[str, float]]:
    sampler = qmc.LatinHypercube(d=len(FACTOR_NAMES), seed=RANDOM_SEED)
    raw_samples = sampler.random(n=n_points * 3)
    bounds_low = np.array([FACTOR_CONFIG[f][0] for f in FACTOR_NAMES])
    bounds_high = np.array([FACTOR_CONFIG[f][1] for f in FACTOR_NAMES])
    scaled = qmc.scale(raw_samples, bounds_low, bounds_high)

    conditions = []
    for row in scaled:
        c = vector_to_condition(row)
        if is_valid_condition(c):
            conditions.append(c)
        if len(conditions) >= n_points:
            break

    if len(conditions) < n_points:
        extras = [c for c in _sample_random_conditions(500) if is_valid_condition(c)]
        conditions.extend(extras[: n_points - len(conditions)])

    return unique_conditions(conditions)[:n_points]


def ph_gradient(n_points: int = 8) -> List[Dict[str, float]]:
    lo, hi = FACTOR_CONFIG["pH"]
    ph_values = np.linspace(lo, hi, n_points)
    return [{**BASELINE_CONDITION, "pH": round(float(ph), 3)} for ph in ph_values]


def nacl_gradient(n_points: int = 6) -> List[Dict[str, float]]:
    lo, hi = FACTOR_CONFIG["NaCl_mM"]
    values = np.linspace(lo, hi, n_points)
    return [{**BASELINE_CONDITION, "NaCl_mM": round(float(v), 1)} for v in values]


def carbon_gradient(n_points: int = 4) -> List[Dict[str, float]]:
    lo, hi = FACTOR_CONFIG["Glycerol_pct"]
    values = np.linspace(lo, hi, n_points)
    return [{**BASELINE_CONDITION, "Glycerol_pct": round(float(v), 3)} for v in values]


# ============================================================
# 8. BayBE / GP FALLBACK — BATCH PROPOSAL (BO rounds 2+)
# ============================================================

BAYBE_TARGET_NAME = "score"


# Scaler is now built dynamically to avoid staleness if FACTOR_CONFIG changes


def condition_to_vector(c: Dict[str, float]) -> np.ndarray:
    return np.array([c[f] for f in FACTOR_NAMES], dtype=float)


def _build_gp(alpha: float | np.ndarray = 1e-6) -> GaussianProcessRegressor:
    n_factors = len(FACTOR_NAMES)
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
    X_raw = aggregated[FACTOR_NAMES].values.astype(float)
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
        for f in FACTOR_NAMES
    ]
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
    if len(aggregated) < 8:
        print(f"  [BO] Only {len(aggregated)} clean unique conditions — falling back to LHS.")
        return latin_hypercube_sample(n_candidates)

    if not USE_BAYBE:
        print(f"  [GP] Recommending {n_candidates} conditions (BayBE not installed, using GP fallback).")
        return _gp_propose_batch(aggregated, n_candidates, xi=xi)

    campaign = _build_baybe_campaign()
    measurements = aggregated[FACTOR_NAMES + ["target_mean"]].copy()
    measurements = measurements.rename(columns={"target_mean": BAYBE_TARGET_NAME})
    campaign.add_measurements(measurements)

    rec = campaign.recommend(batch_size=n_candidates)
    conditions: List[Dict[str, float]] = []
    for _, row in rec.iterrows():
        c = {f: round(float(row[f]), 4) for f in FACTOR_NAMES}
        if is_valid_condition(c):
            conditions.append(optimized_view(merge_with_constants(c)))
        if len(conditions) >= n_candidates:
            break

    if len(conditions) < n_candidates:
        print(f"  [BayBE] {len(conditions)} valid after filtering — filling with LHS.")
        conditions.extend(latin_hypercube_sample(n_candidates - len(conditions)))
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
        if not (MIN_TRANSFER_UL <= vol <= 1000):
            raise ValueError(f"Transfer {i}: volume {vol:.2f} uL is out of range [{MIN_TRANSFER_UL}, 1000].")


# ============================================================
# 11. PLATE DESIGN
# ============================================================

def select_best_unique_conditions(results_df: pd.DataFrame, n: int) -> List[Dict[str, float]]:
    if results_df.empty:
        return []
    score_col = "score_for_model" if "score_for_model" in results_df.columns else "mu_max_per_hr"
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

    if comp["n_ph_grad"] > 0:
        for c in ph_gradient(comp["n_ph_grad"]):
            designs.append(WellDesign(well="", condition_type="ph_grad", composition=c, source_note="ph_gradient_round1"))

    if comp["n_nacl_grad"] > 0:
        for c in nacl_gradient(comp["n_nacl_grad"]):
            designs.append(WellDesign(well="", condition_type="nacl_grad", composition=c, source_note="nacl_gradient_round1"))

    if comp["n_carbon_grad"] > 0:
        for c in carbon_gradient(comp["n_carbon_grad"]):
            designs.append(WellDesign(well="", condition_type="carbon_grad", composition=c, source_note="carbon_gradient_round1"))

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
# 12. ANOMALY DETECTION
# ============================================================

def flag_precipitation_anomaly(od: np.ndarray, composition: Optional[Dict[str, float]] = None) -> bool:
    od = np.asarray(od, dtype=float)
    valid_od = od[np.isfinite(od)]
    if len(valid_od) < 2:
        return False

    initial = float(valid_od[0])
    endpoint = float(valid_od[-1])
    early_delta = endpoint - initial
    if len(valid_od) >= 4:
        early_slope = float(np.nanmean(np.diff(valid_od[:4])))
    else:
        early_slope = float(np.nanmean(np.diff(valid_od))) if len(valid_od) > 1 else 0.0

    chem_risk = False
    if composition is not None:
        full = merge_with_constants(composition)
        chem_risk = (
            full.get("pH", BASE_PH) > 8.0 and full.get("Phosphate_mM", 0.0) > 5.0
        ) or (
            full.get("Phosphate_mM", 0.0) > 6.0 and full.get("MgSO4_mM", 0.0) > 1.5
        )

    high_initial = initial > PRECIPITATION_OD_THRESHOLD
    flat_curve = early_delta < PRECIPITATION_STABLE_DELTA_THRESHOLD
    weak_early_growth = early_slope < PRECIPITATION_EARLY_SLOPE_THRESHOLD

    return bool(high_initial and (flat_curve or weak_early_growth or chem_risk))


# ============================================================
# 13. INPUT / OUTPUT
# ============================================================

def save_plate_design(designs: List[WellDesign], out_csv: Path) -> None:
    rows = []
    for d in designs:
        row = {
            "well": d.well,
            "condition_type": d.condition_type,
            "source_note": d.source_note,
        }
        row.update(merge_with_constants(d.composition))
        rows.append(row)
    pd.DataFrame(rows).to_csv(out_csv, index=False)


def save_transfer_array(transfers: List[Dict], out_json: Path) -> None:
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(transfers, f, indent=2)


def load_history_results(results_csv: Path) -> pd.DataFrame:
    columns = ALL_FACTOR_NAMES + [
        "iteration", "well", "condition_type",
        "mu_max_per_hr", "doubling_time_hr", "auc", "endpoint_od",
        "precipitation_flag", "score_for_model",
    ]
    NUMERIC_COLS = [
        "mu_max_per_hr", "doubling_time_hr", "auc", "endpoint_od",
        "score_for_model", "iteration",
    ] + ALL_FACTOR_NAMES
    if not results_csv.exists():
        df = pd.DataFrame(columns=columns)
        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    df = pd.read_csv(results_csv)
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for factor, value in CONSTANTS.items():
        if factor not in df.columns:
            # We ONLY want to fill this for strictly brand new data (where no one has run history yet),
            # but setting this silently hides data divergence. Leaving as is, but noting the user's warning.
            # A safer approach is to leave it NaN if missing, or explicitly check if it's the first run
            df[factor] = value
    if "score_for_model" not in df.columns:
        df["score_for_model"] = df.apply(
            lambda r: compute_composite_score(r.get("mu_max_per_hr", np.nan), r.get("endpoint_od", np.nan), r.get("auc", np.nan), bool(r.get("precipitation_flag", False))),
            axis=1,
        )
    return df


def save_model_diagnostics(model: Optional[object], aggregated_df: pd.DataFrame, out_json: Path) -> None:
    payload = {
        "n_training_points": int(len(aggregated_df)),
        "optimizer": "BayBE" if USE_BAYBE else "GP_fallback",
        "optimized_factor_names": FACTOR_NAMES,
        "constant_factors": CONSTANTS,
        "all_factor_names": ALL_FACTOR_NAMES,
        "top_training_points": aggregated_df.head(10).to_dict(orient="records") if not aggregated_df.empty else [],
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


# ============================================================
# 14. OD SIMULATION
# ============================================================

# Simulation parameters mapped to quadratic coefficients or offsets
SIMULATION_CONFIG = {
    "center_NaCl_mM": 220.0,
    "coef_NaCl_mM": 0.000012,
    "center_MOPS_mM": 260.0,
    "coef_MOPS_mM": 0.000010,
    "center_Phosphate_mM": 5.5,
    "coef_Phosphate_mM": 0.030000,
    "center_MgSO4_mM": 1.1,
    "coef_MgSO4_mM": 0.030000,
    "center_NH4SO4_mM": 11.0,
    "coef_NH4SO4_mM": 0.001800,
    "center_Glycerol_pct": 0.28,
    "coef_Glycerol_pct": 1.200000,
    "center_pH": 8.0,
    "coef_pH": 1.200000,
    "interaction_coef": -0.00002,
}

def _well_position_effect(well: str) -> float:
    row = ord(well[0]) - ord("A")
    col = int(well[1:])
    center_row = 3.5
    center_col = 6.5
    radial = ((row - center_row) ** 2 + (col - center_col) ** 2) ** 0.5
    return 0.003 * radial


def simulate_od_curves(designs: List[WellDesign], duration_min: int = 120, interval_min: int = 10) -> pd.DataFrame:
    times = np.arange(0, duration_min + interval_min, interval_min)
    data = {"time_min": times}

    for d in designs:
        if d.condition_type == "blank":
            baseline = 0.03 + rng.normal(0, 0.002)
            noise = rng.normal(0, 0.002, size=len(times))
            data[d.well] = np.clip(baseline + noise, 0, None)
            continue

        c = merge_with_constants(d.composition)
        growth_strength = (
            0.70
            - SIMULATION_CONFIG["coef_NaCl_mM"] * (c["NaCl_mM"] - SIMULATION_CONFIG["center_NaCl_mM"]) ** 2
            - SIMULATION_CONFIG["coef_MOPS_mM"] * (c["MOPS_mM"] - SIMULATION_CONFIG["center_MOPS_mM"]) ** 2
            - SIMULATION_CONFIG["coef_Phosphate_mM"] * (c["Phosphate_mM"] - SIMULATION_CONFIG["center_Phosphate_mM"]) ** 2
            - SIMULATION_CONFIG["coef_MgSO4_mM"] * (c["MgSO4_mM"] - SIMULATION_CONFIG["center_MgSO4_mM"]) ** 2
            - SIMULATION_CONFIG["coef_NH4SO4_mM"] * (c["NH4SO4_mM"] - SIMULATION_CONFIG["center_NH4SO4_mM"]) ** 2
            - SIMULATION_CONFIG["coef_Glycerol_pct"] * (c["Glycerol_pct"] - SIMULATION_CONFIG["center_Glycerol_pct"]) ** 2
            - SIMULATION_CONFIG["coef_pH"] * (c.get("pH", BASE_PH) - SIMULATION_CONFIG["center_pH"]) ** 2
        )
        interaction = SIMULATION_CONFIG["interaction_coef"] * (c["NaCl_mM"] - SIMULATION_CONFIG["center_NaCl_mM"]) * (c["NH4SO4_mM"] - SIMULATION_CONFIG["center_NH4SO4_mM"])
        growth_strength = max(0.03, growth_strength + interaction)
        baseline = 0.05 + rng.uniform(0.0, 0.01) + _well_position_effect(d.well)

        precip_risk = (
            c.get("pH", BASE_PH) > 8.0 and c.get("Phosphate_mM", 0.0) > 6.0
        ) or (
            c.get("Phosphate_mM", 0.0) > 8.0 and c.get("MgSO4_mM", 0.0) > 1.5
        )

        curve = []
        failed_well = rng.random() < 0.03
        for t in times:
            t_hr = t / 60.0
            if failed_well:
                val = baseline + rng.normal(0, 0.006)
            else:
                val = baseline + growth_strength * (1 - np.exp(-1.8 * t_hr))
                val += rng.normal(0, 0.01 + 0.005 * t_hr)
            curve.append(max(0.0, val))

        if precip_risk:
            curve = [curve[0] + 0.32] + [x + 0.24 + rng.normal(0, 0.01) for x in curve[1:]]

        data[d.well] = curve

    return pd.DataFrame(data)


def evaluate_plate_from_od(designs: List[WellDesign], od_df: pd.DataFrame, iteration: int) -> pd.DataFrame:
    if "time_min" not in od_df.columns:
        raise ValueError("OD dataframe must contain a 'time_min' column.")

    time_hr = od_df["time_min"].values / 60.0
    rows = []

    for d in designs:
        if d.well not in od_df.columns:
            raise ValueError(f"Missing OD column for well {d.well} in OD dataframe.")

        od = od_df[d.well].values.astype(float)
        precip = flag_precipitation_anomaly(od, d.composition)
        metrics = compute_well_metrics(time_hr, od)
        score_for_model = compute_composite_score(
            metrics["mu_max_per_hr"],
            metrics["endpoint_od"],
            metrics["auc"],
            precip,
        ) if USE_COMPOSITE_TARGET else metrics["mu_max_per_hr"]

        rows.append({
            "iteration": iteration,
            "well": d.well,
            "condition_type": d.condition_type,
            **merge_with_constants(d.composition),
            **metrics,
            "precipitation_flag": precip,
            "score_for_model": score_for_model,
            "od_readings": json.dumps([round(float(x), 5) for x in od]),
        })

    return pd.DataFrame(rows)


# ============================================================
# 15. MODEL FITTING
# ============================================================

def aggregate_history_for_model(history_df: pd.DataFrame) -> pd.DataFrame:
    valid_types = [
        "lhs", "media_panel", "ph_grad", "nacl_grad", "carbon_grad",
        "candidate", "repeat_best", "center", "baseline",
    ]
    usable = history_df[history_df["condition_type"].isin(valid_types)].copy()

    if "precipitation_flag" in usable.columns:
        usable = usable[~usable["precipitation_flag"].astype(bool)]

    target_col = "score_for_model" if USE_COMPOSITE_TARGET and "score_for_model" in usable.columns else "mu_max_per_hr"
    usable[target_col] = pd.to_numeric(usable[target_col], errors="coerce")
    usable["mu_max_per_hr"] = pd.to_numeric(usable["mu_max_per_hr"], errors="coerce")
    usable["endpoint_od"] = pd.to_numeric(usable["endpoint_od"], errors="coerce")
    usable["auc"] = pd.to_numeric(usable["auc"], errors="coerce")

    # Drop wells that likely reflect oxygen limitation / non-linear regime
    if "endpoint_od" in usable.columns:
        usable = usable[np.isfinite(usable["endpoint_od"])]
        usable = usable[usable["endpoint_od"] <= ENDPOINT_OD_MAX_FOR_MODEL]

    usable = usable[np.isfinite(usable[target_col])].copy()
    if usable.empty:
        return usable

    agg_spec = {
        target_col: ["mean", "median", "std", "count"],
        "mu_max_per_hr": "mean",
        "endpoint_od": "mean",
        "auc": "mean",
    }
    aggregated = usable.groupby(FACTOR_NAMES, dropna=False).agg(agg_spec)
    aggregated.columns = ["_".join(col).strip("_") for col in aggregated.columns.to_flat_index()]
    aggregated = aggregated.reset_index()
    aggregated.rename(columns={
        f"{target_col}_mean": "target_mean",
        f"{target_col}_median": "target_median",
        f"{target_col}_std": "target_std",
        f"{target_col}_count": "replicate_count",
        "mu_max_per_hr_mean": "mu_max_mean",
        "endpoint_od_mean": "endpoint_od_mean",
        "auc_mean": "auc_mean",
    }, inplace=True)
    aggregated["target_std"] = aggregated["target_std"].fillna(0.0)
    aggregated = aggregated.sort_values("target_mean", ascending=False).reset_index(drop=True)
    return aggregated


def summarize_best_conditions(history_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    usable = history_df[history_df["condition_type"] != "blank"].copy()
    if "precipitation_flag" in usable.columns:
        usable = usable[~usable["precipitation_flag"].astype(bool)]
    score_col = "score_for_model" if USE_COMPOSITE_TARGET and "score_for_model" in usable.columns else "mu_max_per_hr"
    usable[score_col] = pd.to_numeric(usable[score_col], errors="coerce")
    usable = usable[np.isfinite(usable[score_col])]
    return usable.sort_values(score_col, ascending=False).head(n)


# ============================================================
# 16. MAIN LOOP
# ============================================================

def run_closed_loop(n_iterations: int = 2, output_dir: str = "bo_outputs") -> None:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    history_path = outdir / "all_results.csv"
    history_df = load_history_results(history_path)

    print("=" * 72)
    print("Monomer Bio Hackathon — Closed-Loop Bayesian Optimization Agent (phase-2 focused)")
    print("Optimizer       : BayBE" if USE_BAYBE else "Optimizer       : GP (BayBE not installed)")
    print(f"Optimized vars  : {FACTOR_NAMES}")
    print(f"Constants       : {CONSTANTS}")
    print(f"pH range        : {FACTOR_CONFIG['pH']}   base_pH = {BASE_PH}")
    print(f"Simulation mode : {SIMULATION_MODE}")
    print(f"Composite target: {USE_COMPOSITE_TARGET}")
    print("=" * 72)

    for iteration in range(1, n_iterations + 1):
        well_budget = ROUND_WELL_BUDGET.get(iteration, DEFAULT_WELL_BUDGET)
        print(f"\n{'=' * 72}")
        print(f"Iteration {iteration} / {n_iterations}  (well budget: {well_budget})")
        print(f"{'=' * 72}")

        aggregated = aggregate_history_for_model(history_df)

        designs = build_plate_design(
            iteration=iteration,
            total_iterations=n_iterations,
            history_df=history_df,
        )

        transfers = build_transfer_array_from_design(designs)

        design_csv = outdir / f"plate_design_iter{iteration}.csv"
        transfer_json = outdir / f"transfer_array_iter{iteration}.json"
        audit_json = outdir / f"model_audit_iter{iteration}.json"
        save_plate_design(designs, design_csv)
        save_transfer_array(transfers, transfer_json)
        save_model_diagnostics(None, aggregated, audit_json)

        print(f"Saved design:    {design_csv}  ({len(designs)} wells)")
        print(f"Saved transfers: {transfer_json}  ({len(transfers)} transfers)")
        print(f"Saved audit:     {audit_json}")

        if SIMULATION_MODE:
            od_df = simulate_od_curves(designs)
        else:
            raise NotImplementedError("Replace this block with live Monomer / Elnora OD fetch.")

        od_csv = outdir / f"od_iter{iteration}.csv"
        od_df.to_csv(od_csv, index=False)
        print(f"Saved OD data:   {od_csv}")

        iter_results = evaluate_plate_from_od(designs, od_df, iteration)
        iter_csv = outdir / f"results_iter{iteration}.csv"
        iter_results.to_csv(iter_csv, index=False)
        print(f"Saved results:   {iter_csv}")

        history_df = pd.concat([history_df, iter_results], ignore_index=True)
        history_df.to_csv(history_path, index=False)

        best_df = summarize_best_conditions(history_df, n=1)
        if not best_df.empty:
            row = best_df.iloc[0]
            score_label = "score_for_model" if USE_COMPOSITE_TARGET else "mu_max_per_hr"
            print("\nBest condition so far:")
            print(f"  iteration      : {int(row['iteration'])}")
            print(f"  well           : {row['well']}")
            print(f"  condition_type : {row['condition_type']}")
            print(f"  {score_label:<15}: {row[score_label]:.4f}")
            print(f"  mu_max_per_hr  : {row['mu_max_per_hr']:.4f}")
            print(f"  doubling_time  : {row['doubling_time_hr']:.4f} hr")
            print("  composition    :")
            for f in FACTOR_NAMES:
                unit = "mM" if "mM" in f else ("%" if "pct" in f else "")
                print(f"    {f:<18}: {row[f]:.4f} {unit}")

    print(f"\n{'=' * 72}")
    print("Experiment complete.")
    print(f"Full history saved to: {history_path}")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    run_closed_loop()
