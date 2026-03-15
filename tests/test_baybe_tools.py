"""Tests for BayBE optimization tool."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_baybe_propose_returns_conditions():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=5, round_number=2)
    assert "proposed_conditions" in result
    assert len(result["proposed_conditions"]) == 5
    assert result["n_historical_conditions"] > 0


def test_baybe_conditions_have_required_fields():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=3, round_number=2)
    for cond in result["proposed_conditions"]:
        assert "base_media" in cond
        assert "base_media_vol" in cond
        assert "predicted_growth_rate_per_hr" in cond


def test_baybe_predicted_rates_are_positive():
    from tools.baybe_tools import baybe_propose
    result = baybe_propose(n_proposals=5)
    for cond in result["proposed_conditions"]:
        rate = cond.get("predicted_growth_rate_per_hr", 0)
        # NaN is acceptable if GP can't predict, but non-NaN should be positive
        if rate == rate:  # not NaN
            assert rate > 0, f"Predicted rate should be positive: {rate}"
