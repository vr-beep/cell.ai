"""Random screening — LHS sampling for initial exploration."""
from __future__ import annotations

import numpy as np
from scipy.stats import qmc

RANDOM_SEED = 42
TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL

DEFAULT_RANGES = {
    "base_media_vol": (100, 160),
    "yeast_extract": (0, 30),
    "tryptone": (0, 30),
    "mops": (0, 20),
    "na_l_glut": (0, 15),
    "kh2po4": (0, 10),
    "glucose": (0, 20),
}

BASE_MEDIA_OPTIONS = ["Semi-Defined Media", "High Buffer Defined Media"]


def latin_hypercube_screen(
    n_conditions: int = 10,
    factor_ranges: dict | None = None,
    base_media: str | None = None,
) -> dict:
    ranges = factor_ranges or DEFAULT_RANGES
    factors = list(ranges.keys())
    n_dim = len(factors)

    sampler = qmc.LatinHypercube(d=n_dim, seed=RANDOM_SEED)
    raw = sampler.random(n=n_conditions * 5)

    bounds_low = np.array([ranges[f][0] for f in factors])
    bounds_high = np.array([ranges[f][1] for f in factors])
    scaled = qmc.scale(raw, bounds_low, bounds_high)

    rng = np.random.default_rng(RANDOM_SEED)
    conditions = []

    for row in scaled:
        c = {f: round(float(v), 1) for f, v in zip(factors, row)}
        vol_sum = sum(c.values())
        if vol_sum > REAGENT_VOL_UL:
            continue
        c["base_media"] = base_media or rng.choice(BASE_MEDIA_OPTIONS)
        c["water"] = round(REAGENT_VOL_UL - vol_sum, 1)
        c["cells"] = CELL_VOL_UL
        c["total"] = TOTAL_VOL_UL
        conditions.append(c)
        if len(conditions) >= n_conditions:
            break

    return {"n_conditions": len(conditions), "method": "latin_hypercube", "conditions": conditions}
