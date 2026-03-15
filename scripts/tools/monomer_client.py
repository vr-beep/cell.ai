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


def _mcp_call(url: str, method: str, params: dict, token: str = "") -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": method, "arguments": params},
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")
    return data.get("result", {})


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

    # Real Monomer MCP
    try:
        data = _mcp_call(MONITOR_URL, "get_plate_observations",
                         {"plate_name": plate_id}, token=MONITOR_TOKEN)
        return {"plate_id": plate_id, "source": "monomer_mcp", "raw": data}
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
        result = _mcp_call(AUTOPLAT_URL, "instantiate_workflow", {
            "definition_name": "hackathon_closed_loop",
            "plate_barcode": plate_barcode,
            "extra_inputs": {
                "transfer_array": json.dumps(transfers),
                "monitoring_wells": json.dumps(monitoring_wells),
            },
            "reason": round_label,
        })
        return {"status": "submitted", "workflow_file": str(output_file), "mcp_result": result}
    except Exception as e:
        return {"status": "saved_locally", "workflow_file": str(output_file), "mcp_error": str(e)}


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
            result = _mcp_call(AUTOPLAT_URL, "get_workflow_instance_details",
                               {"workflow_id": workflow_id})
            if result.get("status") in ("completed", "failed"):
                return result
        except Exception:
            pass
        time.sleep(poll_interval)
    return {"error": "timeout", "workflow_id": workflow_id}
