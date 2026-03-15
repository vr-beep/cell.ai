"""Validation tools — convergence check, precipitation rules."""
from __future__ import annotations

PRECIPITATION_RULES = [
    {"pair": ("CaCl2", "K2HPO4"), "action": "NEVER", "fix": "Use KH2PO4"},
    {"pair": ("CaCl2", "Novel Bio"), "action": "NEVER", "fix": "No CaCl2 with Novel Bio"},
    {"pair": ("MgSO4", "K2HPO4"), "action": "CONDITIONAL", "fix": "Add >=12.5mM citrate or use KH2PO4"},
    {"pair": ("FeSO4", "K2HPO4"), "action": "NEVER", "fix": "Use KH2PO4 at low iron"},
]

def check_precipitation(conditions: list[dict]) -> dict:
    """Check conditions for known precipitation risks."""
    warnings = []
    for i, cond in enumerate(conditions):
        components = set(
            k for k, v in cond.items()
            if k not in ("base_media", "base_media_vol", "condition", "water", "cells")
            and v and float(v) > 0
        )
        base = cond.get("base_media", "")
        for rule in PRECIPITATION_RULES:
            a, b = rule["pair"]
            a_low = a.lower().replace(" ", "_")
            b_low = b.lower().replace(" ", "_")
            if (a_low in components or a in base) and (b_low in components or b in base):
                warnings.append({
                    "condition": i,
                    "rule": rule["action"],
                    "fix": rule["fix"],
                    "pair": list(rule["pair"]),
                })
    return {"n_warnings": len(warnings), "warnings": warnings}


def check_convergence(current_best_rate: float, current_best_se: float, previous_best_rate: float, previous_best_se: float) -> dict:
    ci_current = (current_best_rate - 1.96 * current_best_se, current_best_rate + 1.96 * current_best_se)
    ci_previous = (previous_best_rate - 1.96 * previous_best_se, previous_best_rate + 1.96 * previous_best_se)
    overlap = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]
    improvement_pct = ((current_best_rate - previous_best_rate) / previous_best_rate * 100) if previous_best_rate > 0 else float("inf")
    return {
        "converged": overlap,
        "current_ci": [round(ci_current[0], 4), round(ci_current[1], 4)],
        "previous_ci": [round(ci_previous[0], 4), round(ci_previous[1], 4)],
        "improvement_pct": round(improvement_pct, 2),
        "recommendation": "STOP — converged" if overlap else "CONTINUE — improvement detected",
    }
