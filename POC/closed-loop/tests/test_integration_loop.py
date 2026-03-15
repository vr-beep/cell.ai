"""Integration test: full simulated closed loop without Anthropic API."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["SIMULATION_MODE"] = "1"

PLATE_ID = "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ"


def test_full_tool_chain():
    from tools.monomer_client import fetch_results, monomer_submit, wait_for_workflow
    from tools.analyzer import analyze_results
    from tools.baybe_tools import baybe_propose
    from tools.compiler import compile_protocol
    from tools.validators import check_convergence

    # Step 1: Fetch Round 1 results
    r1 = fetch_results(PLATE_ID)
    assert r1["n_wells"] == 10
    best_r1 = r1["results"][0]["growth_rate"]
    assert best_r1 > 1.5

    # Step 2: Analyze
    analysis = analyze_results(f"data/{PLATE_ID}_growth.csv")
    assert analysis["best_growth_rate"] > 1.5

    # Step 3: BayBE proposes Round 2
    proposals = baybe_propose(n_proposals=5, round_number=2)
    assert len(proposals["proposed_conditions"]) == 5

    # Step 4: Compile to transfer_array
    wells = ["B2", "B3", "B4", "B5", "B6"]
    protocol = compile_protocol(json.dumps(proposals["proposed_conditions"]), wells)
    assert len(protocol["errors"]) == 0
    assert protocol["n_transfers"] > 0

    # Step 5: Submit to simulator
    submit = monomer_submit(
        transfer_array_json=json.dumps(protocol["transfer_array"]),
        monitoring_wells=wells,
        plate_barcode="SIM_R2_PLATE",
        round_label="round_2",
    )
    wf_id = submit.get("workflow_id")
    assert wf_id

    # Step 6: Wait for completion
    status = wait_for_workflow(wf_id, timeout=15)
    assert status["status"] == "completed"

    # Step 7: Fetch simulated results
    r2 = fetch_results("SIM_R2_PLATE")
    assert r2["n_wells"] > 0
    best_r2 = r2["results"][0]["growth_rate"]
    assert best_r2 > 0

    # Step 8: Check convergence
    conv = check_convergence(
        current_best_rate=best_r2, current_best_se=0.1,
        previous_best_rate=best_r1, previous_best_se=0.1,
    )
    assert "converged" in conv
    print(f"\nRound 1 best: {best_r1}/hr → Round 2 best: {best_r2}/hr")
    print(f"Converged: {conv['converged']} ({conv['recommendation']})")
