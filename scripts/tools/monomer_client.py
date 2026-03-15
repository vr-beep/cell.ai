"""Monomer MCP client — fetch results and submit workflows.

Set SIMULATION_MODE=1 to use GP-based growth simulator instead of real Monomer.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).parent.parent.parent / "data"

SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "0") == "1"
AUTOPLAT_URL = "http://192.168.68.60:8080/mcp"
MONITOR_URL = "https://backend-staging.monomerbio.com/mcp"
MONITOR_TOKEN = os.environ.get("MONOMER_TOKEN", "")

_simulator = None


def _get_simulator():
    global _simulator
    if _simulator is None:
        from tools.growth_simulator import GrowthSimulator
        _simulator = GrowthSimulator(data_dir=DATA_DIR)
    return _simulator


def _mcp_call_cloud(method: str, params: dict) -> dict:
    """Direct MCP call to monomer-cloud (supports named tools)."""
    headers = {"Content-Type": "application/json"}
    if MONITOR_TOKEN:
        headers["Authorization"] = f"Bearer {MONITOR_TOKEN}"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": params},
    }
    resp = requests.post(MONITOR_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")
    return data.get("result", {})


def _mcp_call_autoplat(tool_name: str, arguments: dict) -> dict:
    """Call autoplat MCP via search_tools + call_tool pattern.

    Autoplat uses dynamic tool discovery — tools are called via the
    generic call_tool endpoint, not directly.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "call_tool", "arguments": {
            "name": tool_name,
            "arguments": arguments,
        }},
    }
    resp = requests.post(AUTOPLAT_URL, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"Autoplat MCP error: {data['error']}")
    result = data.get("result", {})
    # Autoplat wraps results in {"result": ...}
    if isinstance(result, dict) and "result" in result:
        return result["result"]
    return result


def fetch_results(plate_id: str) -> dict:
    """Fetch growth rate results for a plate."""
    # Try local CSV first
    growth_csv = DATA_DIR / f"{plate_id}_growth.csv"
    if growth_csv.exists():
        df = pd.read_csv(growth_csv)
        results = []
        for _, row in df.iterrows():
            results.append({
                "well": row["well"],
                "condition": row["condition_id"],
                "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
                "max_od600": round(float(row["max_absorbance_OD600"]), 4),
            })
        results.sort(key=lambda x: x["growth_rate"], reverse=True)
        return {"plate_id": plate_id, "source": "local_csv",
                "n_wells": len(results), "results": results}

    # Simulation mode
    if SIMULATION_MODE:
        sim = _get_simulator()
        obs = sim.get_plate_observations(plate_id)
        if obs.get("observations"):
            results = [
                {"well": w["well"], "condition": w["condition_id"],
                 "growth_rate": w["growth_rate_per_hr"],
                 "max_od600": w["max_absorbance_OD600"]}
                for w in obs["observations"]
            ]
            results.sort(key=lambda x: x["growth_rate"], reverse=True)
            return {"plate_id": plate_id, "source": "simulator",
                    "n_wells": len(results), "results": results}
        return {"plate_id": plate_id, "source": "simulator", "status": "no_data"}

    # Real Monomer MCP — try cloud first (structured data), then autoplat
    try:
        data = _mcp_call_cloud("get_plate_observations", {"plate_name": plate_id})
        return {"plate_id": plate_id, "source": "monomer_cloud", "raw": data}
    except Exception as e:
        return {"error": f"Cannot fetch results for {plate_id}: {e}"}


def monomer_submit(transfer_array_json: str, monitoring_wells: list[str],
                   plate_barcode: str, round_label: str = "") -> dict:
    """Submit a workflow."""
    transfers = json.loads(transfer_array_json) if isinstance(transfer_array_json, str) else transfer_array_json

    if SIMULATION_MODE:
        sim = _get_simulator()
        result = sim.instantiate_workflow(transfers, monitoring_wells, plate_barcode)
        return {"status": "submitted_to_simulator", **result}

    # Save locally + try MCP
    output_dir = DATA_DIR.parent / "workflows"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"workflow_{round_label or 'next'}.json"
    with open(output_file, "w") as f:
        json.dump({"transfer_array": transfers, "monitoring_wells": monitoring_wells,
                    "plate_barcode": plate_barcode}, f, indent=2)

    try:
        # Step 1: Create workflow definition file on workcell
        _mcp_call_autoplat("create_workflow_definition_file", {
            "file_name": f"cellai_{round_label or 'next'}.py",
            "code_content": _generate_workflow_code(transfers, monitoring_wells, plate_barcode),
        })

        # Step 2: Validate
        validation = _mcp_call_autoplat("validate_workflow_definition_file", {
            "file_name": f"cellai_{round_label or 'next'}.py",
            "inputs": {
                "plate_barcode": plate_barcode,
                "reagent_name": "Team Elnora Reagent Stocks",
                "cell_stock_plate_barcode": "Team Elnora Culture Stock Plate",
            },
        })
        if not validation.get("success", False):
            return {"status": "validation_failed", "workflow_file": str(output_file),
                    "error": validation.get("error", "Unknown validation error")}

        # Step 3: Register
        reg = _mcp_call_autoplat("register_workflow_definition", {
            "name": f"CellAI {round_label or 'Orchestrator Round'}",
            "file_name": f"cellai_{round_label or 'next'}.py",
        })
        def_id = reg.get("definition_id")

        # Step 4: Instantiate
        result = _mcp_call_autoplat("instantiate_workflow", {
            "definition_id": def_id,
            "inputs": {
                "plate_barcode": plate_barcode,
                "reagent_name": "Team Elnora Reagent Stocks",
                "cell_stock_plate_barcode": "Team Elnora Culture Stock Plate",
            },
            "reason": round_label,
        })
        return {"status": "submitted", "workflow_file": str(output_file), "mcp_result": result}
    except Exception as e:
        return {"status": "saved_locally", "workflow_file": str(output_file), "mcp_error": str(e)}


def _generate_workflow_code(transfers: list, monitoring_wells: list, plate_barcode: str) -> str:
    """Generate workflow definition Python code for the workcell DSL."""
    import textwrap
    transfer_json = json.dumps(transfers)
    wells_json = json.dumps(monitoring_wells)
    return textwrap.dedent(f'''\
        from src.platform.core_domain.units import Time
        from src.workflows.workflow_definition_dsl.workflow_definition_descriptor import (
            MoreThanConstraint, RoutineReference, WorkflowDefinitionDescriptor,
        )
        import json

        def build_definition(
            plate_barcode: str = "{plate_barcode}",
            reagent_name: str = "Team Elnora Reagent Stocks",
            cell_stock_plate_barcode: str = "Team Elnora Culture Stock Plate",
            monitoring_readings: int = 9,
            monitoring_interval_minutes: int = 10,
        ) -> WorkflowDefinitionDescriptor:
            transfer_array = json.loads('{transfer_json}')
            monitoring_wells = json.loads('{wells_json}')

            workflow = WorkflowDefinitionDescriptor(
                description="CellAI orchestrator: {{len(transfers)}} transfers, {{len(monitoring_wells)}} wells"
            )

            transfer = RoutineReference(
                routine_name="Hackathon Transfer Samples",
                routine_parameters={{
                    "reagent_name": reagent_name,
                    "experiment_plate_barcode": plate_barcode,
                    "cell_culture_stock_plate_barcode": cell_stock_plate_barcode,
                    "transfer_array": transfer_array,
                }},
            )
            workflow.add_routine("transfer", transfer)

            keys = []
            for i in range(monitoring_readings):
                key = f"od600_{{i}}"
                workflow.add_routine(key, RoutineReference(
                    routine_name="Measure Experiment Plate Absorbance",
                    routine_parameters={{
                        "culture_plate_barcode": plate_barcode,
                        "method_name": "96wp_od600",
                        "wells_to_process": monitoring_wells,
                    }},
                ))
                keys.append(key)

            workflow.space_out_routines(keys, Time(f"{{monitoring_interval_minutes}} minutes"))
            workflow.add_time_constraint(MoreThanConstraint(
                from_start="transfer", to_start=keys[0], value=Time("1 minute"),
            ))

            return workflow
    ''')


def wait_for_workflow(workflow_id: str, timeout: int = 30, poll_interval: float = 1.0) -> dict:
    """Poll workflow status until complete or timeout."""
    if SIMULATION_MODE:
        sim = _get_simulator()
        start = time.time()
        while time.time() - start < timeout:
            status = sim.get_workflow_instance_details(workflow_id)
            if status.get("status") == "completed":
                return status
            time.sleep(poll_interval)
        return {"error": "timeout", "workflow_id": workflow_id}

    start = time.time()
    while time.time() - start < timeout:
        try:
            result = _mcp_call_autoplat("get_workflow_instance_details",
                                        {"instance_uuid": workflow_id})
            status = result.get("status", "")
            if status in ("completed", "failed", "cancelled"):
                return result
        except Exception:
            pass
        time.sleep(poll_interval)
    return {"error": "timeout", "workflow_id": workflow_id}
