"""Tests for GP-based growth simulator."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

DATA_DIR = Path(__file__).parent.parent / "data"


def test_simulator_initializes_with_round1_data():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)
    assert sim._gp is not None, "GP should be fitted on Round 1 data"


def test_different_conditions_give_different_rates():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    # HB-1 like condition (high tryptone, some glutamate)
    cond_a = {"base_media_vol": 110, "yeast_extract": 14, "tryptone": 26,
              "mops": 0, "na_l_glut": 10, "kh2po4": 0, "glucose": 0}
    # Very different condition
    cond_b = {"base_media_vol": 130, "yeast_extract": 0, "tryptone": 0,
              "mops": 18, "na_l_glut": 0, "kh2po4": 10, "glucose": 18}

    rate_a = sim.predict_growth_rate(cond_a)
    rate_b = sim.predict_growth_rate(cond_b)

    assert rate_a > 0
    assert rate_b > 0
    assert abs(rate_a - rate_b) > 0.01, f"Rates should differ: {rate_a} vs {rate_b}"


def test_workflow_lifecycle():
    from tools.growth_simulator import GrowthSimulator, DELAY_SECONDS
    sim = GrowthSimulator(data_dir=DATA_DIR)

    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
        {"src_plate": "reagent", "src_well": "A1", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 14},
    ]

    result = sim.instantiate_workflow(transfers, ["B2"], "TEST_PLATE_1")
    wf_id = result["workflow_id"]
    assert wf_id

    # Initially in_progress
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] == "in_progress"

    # Wait for completion
    time.sleep(DELAY_SECONDS + 1)
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] == "completed"

    # Results available
    obs = sim.get_plate_observations("TEST_PLATE_1")
    assert len(obs["observations"]) > 0
    assert obs["observations"][0]["growth_rate_per_hr"] > 0


def test_simulator_generates_od600_timeseries():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    ts = sim._generate_od600_timeseries(growth_rate=1.5, n_points=9)
    assert len(ts) == 9
    assert all("time_hr" in p and "od600" in p for p in ts)
    # OD should generally increase over time
    assert ts[-1]["od600"] > ts[0]["od600"]


def test_simulator_refits_gp_after_new_data():
    from tools.growth_simulator import GrowthSimulator, DELAY_SECONDS
    sim = GrowthSimulator(data_dir=DATA_DIR)

    n_before = len(sim._history)

    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "C3", "volume": 110},
    ]
    result = sim.instantiate_workflow(transfers, ["C3"], "REFIT_PLATE")
    time.sleep(DELAY_SECONDS + 1)
    sim.get_workflow_instance_details(result["workflow_id"])

    assert len(sim._history) > n_before, "History should grow after new data"


def test_extrapolation_returns_baseline_with_noise():
    from tools.growth_simulator import GrowthSimulator
    sim = GrowthSimulator(data_dir=DATA_DIR)

    # Extreme condition far from training data
    cond_extreme = {"base_media_vol": 180, "yeast_extract": 0, "tryptone": 0,
                    "mops": 0, "na_l_glut": 0, "kh2po4": 0, "glucose": 0}

    rates = [sim.predict_growth_rate(cond_extreme) for _ in range(10)]
    # Should be around baseline (~1.0) with large noise, not extreme values
    mean_rate = sum(rates) / len(rates)
    assert 0.3 < mean_rate < 2.0, f"Extrapolation should stay reasonable: {mean_rate}"
