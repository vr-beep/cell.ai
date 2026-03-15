"""Tests for Monomer client — simulation mode."""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["SIMULATION_MODE"] = "1"

DATA_DIR = Path(__file__).parent.parent / "data"
PLATE_ID = "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ"


def test_fetch_results_from_local_csv():
    from tools.monomer_client import fetch_results
    result = fetch_results(PLATE_ID)
    assert result["source"] in ("local_csv", "simulator")
    assert result["n_wells"] == 10
    assert result["results"][0]["growth_rate"] > 1.5  # best is HB-1


def test_submit_in_simulation_mode():
    from tools.monomer_client import monomer_submit
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
    ]
    result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["B2"],
        plate_barcode="SIM_TEST_PLATE",
        round_label="test_round",
    )
    assert "workflow_id" in result or "status" in result


def test_wait_for_workflow_completes():
    from tools.monomer_client import monomer_submit, wait_for_workflow
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
    ]
    submit_result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["B2"],
        plate_barcode="WAIT_TEST_PLATE",
    )
    wf_id = submit_result.get("workflow_id", "")
    if wf_id:
        status = wait_for_workflow(wf_id, timeout=15, poll_interval=1.0)
        assert status.get("status") == "completed"


def test_fetch_simulated_results_after_workflow():
    from tools.monomer_client import monomer_submit, wait_for_workflow, fetch_results
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "C4", "volume": 110},
        {"src_plate": "reagent", "src_well": "A1", "dst_plate": "experiment",
         "dst_well": "C4", "volume": 20},
    ]
    submit_result = monomer_submit(
        transfer_array_json=json.dumps(transfers),
        monitoring_wells=["C4"],
        plate_barcode="FETCH_SIM_PLATE",
    )
    wf_id = submit_result.get("workflow_id", "")
    if wf_id:
        wait_for_workflow(wf_id, timeout=15)
        result = fetch_results("FETCH_SIM_PLATE")
        assert result.get("n_wells", 0) > 0
        assert result["results"][0]["growth_rate"] > 0
