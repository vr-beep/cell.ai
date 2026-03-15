"""BayBE optimization tool — wraps baybe_opt.py logic for the orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add scripts dir to path for baybe_opt imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from baybe_opt import (
    GrowthRatePredictor,
    load_history,
    propose_conditions,
    format_output,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def baybe_propose(n_proposals: int = 10, round_number: int | None = None) -> dict:
    """Run BayBE optimization and return proposed conditions with predicted growth rates."""
    try:
        history = load_history(str(DATA_DIR))
    except FileNotFoundError as e:
        return {"error": str(e)}

    n_unique = len(history)
    n_media = history["base_media"].nunique()
    rate_range = (float(history["mean_growth_rate_per_hr"].min()),
                  float(history["mean_growth_rate_per_hr"].max()))

    # Run BayBE campaigns
    proposals = propose_conditions(history, n_proposals=n_proposals)

    # Fit GP predictor for growth rate annotations
    predictor = GrowthRatePredictor()
    if len(history) >= 2:
        predictor.fit(history)
        predicted = predictor.predict(proposals)
    else:
        predicted = np.full(len(proposals), np.nan)

    # Format output
    output_df = format_output(proposals, predicted, round_num=round_number)

    # Convert to list of dicts for JSON serialization
    conditions = output_df.to_dict(orient="records")

    return {
        "n_proposals": len(conditions),
        "n_historical_conditions": n_unique,
        "n_media_types": n_media,
        "historical_rate_range": rate_range,
        "proposed_conditions": conditions,
    }
