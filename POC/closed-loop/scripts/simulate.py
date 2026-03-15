#!/usr/bin/env python3
"""Simulate a Monomer experiment from a workflow definition file.

Usage:
    python scripts/simulate.py path/to/workflow.py
    python scripts/simulate.py path/to/workflow.py --delay 0
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.growth_simulator import GrowthSimulator


def extract_transfer_array(workflow_file: str) -> tuple[list[dict], list[str]]:
    """Extract transfer_array and target wells from a workflow .py file."""
    code = Path(workflow_file).read_text()

    # Execute the file to get the build_definition function
    namespace = {}
    # Mock the workcell imports that only exist on the robot
    mock_module = type(sys)("mock")
    mock_module.Time = lambda x: x
    mock_module.MoreThanConstraint = lambda **kw: None
    mock_module.RoutineReference = type("RoutineReference", (), {
        "__init__": lambda self, **kw: setattr(self, "params", kw.get("routine_parameters", {}))
    })
    class MockWDD:
        def __init__(self, **kw):
            self._routines = {}
            self._constraints = []
        def add_routine(self, key, ref):
            self._routines[key] = ref
        def add_time_constraint(self, c):
            self._constraints.append(c)
        def space_out_routines(self, *a, **kw):
            pass
    mock_module.WorkflowDefinitionDescriptor = MockWDD

    sys.modules["src"] = mock_module
    sys.modules["src.platform"] = mock_module
    sys.modules["src.platform.core_domain"] = mock_module
    sys.modules["src.platform.core_domain.units"] = mock_module
    sys.modules["src.workflows"] = mock_module
    sys.modules["src.workflows.workflow_definition_dsl"] = mock_module
    sys.modules["src.workflows.workflow_definition_dsl.workflow_definition_descriptor"] = mock_module

    exec(compile(code, workflow_file, "exec"), namespace)

    build_fn = namespace.get("build_definition")
    if not build_fn:
        print("ERROR: No build_definition() found in file")
        sys.exit(1)

    wf = build_fn()

    # Extract transfer_array from the transfer routine
    transfer_routine = wf._routines.get("transfer")
    if not transfer_routine:
        print("ERROR: No 'transfer' routine found")
        sys.exit(1)

    transfer_array = transfer_routine.params.get("transfer_array", [])

    # Extract target wells from transfer array
    wells = sorted(set(
        t["dst_well"] for t in transfer_array
        if t.get("dst_plate") == "experiment"
    ))

    return transfer_array, wells


def main():
    parser = argparse.ArgumentParser(description="Simulate a Monomer experiment")
    parser.add_argument("workflow_file", help="Path to workflow .py file")
    parser.add_argument("--delay", type=int, default=0, help="Simulated delay in seconds (default: 0)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    # 1. Extract transfer_array
    print(f"Reading: {args.workflow_file}")
    transfer_array, wells = extract_transfer_array(args.workflow_file)
    print(f"Transfers: {len(transfer_array)}")
    print(f"Wells: {wells}")
    print()

    # 2. Submit to simulator
    sim = GrowthSimulator()
    result = sim.instantiate_workflow(transfer_array, wells, "SIM_PLATE")
    wf_id = result["workflow_id"]
    print(f"Workflow submitted: {wf_id}")

    # 3. Wait
    if args.delay > 0:
        print(f"Incubating... ({args.delay}s)")
        time.sleep(args.delay)
    else:
        # Force instant completion
        wf = sim._workflows[wf_id]
        wf.submitted_at = 0
    sim.get_workflow_instance_details(wf_id)

    # 4. Results
    obs = sim.get_plate_observations("SIM_PLATE")

    if args.json:
        print(json.dumps(obs, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"RESULTS")
        print(f"{'='*60}")
        print(f"{'Well':<8} {'Growth Rate (/hr)':<20} {'Max OD600':<12}")
        print(f"{'-'*8} {'-'*20} {'-'*12}")
        for w in sorted(obs["observations"], key=lambda x: -x["growth_rate_per_hr"]):
            print(f"{w['well']:<8} {w['growth_rate_per_hr']:<20.4f} {w['max_absorbance_OD600']:<12.4f}")

        print(f"\nBest: {obs['observations'][0]['well']} "
              f"at {max(w['growth_rate_per_hr'] for w in obs['observations']):.4f}/hr")


if __name__ == "__main__":
    main()
