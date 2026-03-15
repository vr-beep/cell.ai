"""Analyze Monomer growth data: rank conditions, compute CI, check convergence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).parent.parent.parent / "data"


def analyze_results(current_round_csv: str, previous_best_rate: float = 0.0) -> dict:
    """Parse growth CSV, rank by growth rate, compute confidence intervals."""
    growth_path = Path(current_round_csv)
    if not growth_path.exists():
        return {"error": f"File not found: {current_round_csv}"}

    df = pd.read_csv(growth_path)

    # Expected columns from Monomer *_growth.csv
    required = ["well", "condition_id", "growth_rate_per_hr", "max_absorbance_OD600"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"error": f"Missing columns: {missing}"}

    # Rank by growth rate
    ranked = df.sort_values("growth_rate_per_hr", ascending=False).reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)

    # Best condition stats
    best = ranked.iloc[0]
    best_rate = float(best["growth_rate_per_hr"])
    best_condition = str(best["condition_id"])

    # Compute SE if replicates exist (via *_replicates.csv)
    rep_path = growth_path.parent / growth_path.name.replace("_growth.csv", "_replicates.csv")
    best_se = 0.05  # default
    if rep_path.exists():
        rep_df = pd.read_csv(rep_path)
        if "variance_growth_rate_per_hr" in rep_df.columns:
            best_rep = rep_df[rep_df["condition_id"].str.startswith(best_condition.split("_")[0])]
            if not best_rep.empty:
                var = best_rep["variance_growth_rate_per_hr"].iloc[0]
                n = best_rep["n_replicates"].iloc[0] if "n_replicates" in best_rep.columns else 1
                if pd.notna(var) and n > 0:
                    best_se = float(np.sqrt(var) / np.sqrt(n))

    # Convergence check vs previous round
    converged = False
    if previous_best_rate > 0 and best_se > 0:
        ci_current = (best_rate - 1.96 * best_se, best_rate + 1.96 * best_se)
        # Assume same SE for previous (conservative)
        ci_previous = (previous_best_rate - 1.96 * best_se, previous_best_rate + 1.96 * best_se)
        converged = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]

    # Build summary table
    summary_rows = []
    for _, row in ranked.iterrows():
        summary_rows.append({
            "rank": int(row["rank"]),
            "condition": str(row["condition_id"]),
            "well": str(row["well"]),
            "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
            "max_od600": round(float(row["max_absorbance_OD600"]), 4),
        })

    return {
        "n_conditions": len(ranked),
        "best_condition": best_condition,
        "best_growth_rate": round(best_rate, 4),
        "best_se": round(best_se, 4),
        "converged": converged,
        "previous_best_rate": previous_best_rate,
        "ranked_conditions": summary_rows,
    }
