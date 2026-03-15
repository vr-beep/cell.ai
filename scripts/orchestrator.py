"""
Closed-loop media optimization orchestrator.

Uses Anthropic API with tool_use to autonomously:
1. Fetch results from Monomer workcell
2. Analyze growth rates
3. Route to Elnora (early rounds) or BayBE (later rounds)
4. Validate conditions against precipitation rules
5. Compile transfer_array and submit workflow
6. Check convergence → stop or loop
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
DATA_DIR = Path(__file__).parent.parent / "data"
STATE_FILE = DATA_DIR / "orchestrator_state.json"

# Context window management: keep seed + last N tool exchange messages
MAX_TOOL_EXCHANGES = 6  # ~2 rounds of 3 tool calls each

SYSTEM_PROMPT = """You are a closed-loop media optimization agent for V. natriegens.
You have tools to fetch results, analyze data, consult Elnora AI for biological guidance,
run BayBE optimization, validate conditions, compile protocols, and submit to the robot.

IMPORTANT FILE PATHS:
- Growth data CSVs are at: data/<plate_id>_growth.csv (e.g. data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv)
- Always use the plate_id returned by fetch_results to construct the CSV path for analyze_results

WORKFLOW - follow these steps in order:
1. Call fetch_results with the plate_id to get growth data
2. Call analyze_results with the FULL path "data/{plate_id}_growth.csv" and previous_best_rate
3. ROUTING: If n_conditions >= 8, call baybe_propose. If < 8, call elnora_design.
4. Call compile_protocol with the proposed conditions and target wells ["B2","B3","B4","B5","B6","B7","B8","B9","B10","B11"]
5. Call monomer_submit with the transfer_array
6. Call check_convergence to decide whether to stop

If elnora_design fails (CLI error), fall back to baybe_propose.
If baybe_propose fails, fall back to elnora_design.

STOP CONDITION: If check_convergence returns converged=true, stop the loop.

Wells to use: B2-B11 (10 wells, inner wells only to avoid edge effects)."""


def save_state(messages: list, round_info: dict | None = None) -> None:
    """Persist orchestrator state for crash recovery."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "messages": messages,
        "round_info": round_info or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    STATE_FILE.write_text(json.dumps(state, default=str))


def load_state() -> dict | None:
    """Load persisted orchestrator state if available."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return None


def trim_messages(messages: list) -> list:
    """Keep system seed + last N tool exchanges to prevent context overflow."""
    if len(messages) <= MAX_TOOL_EXCHANGES + 2:
        return messages
    seed = messages[:1]
    recent = messages[-(MAX_TOOL_EXCHANGES):]
    summary = {
        "role": "user",
        "content": (
            f"[Previous tool exchanges trimmed. "
            f"{len(messages) - len(recent) - 1} messages removed to manage context.]"
        ),
    }
    return seed + [summary] + recent


def get_tools() -> list[dict]:
    """Return tool definitions for Anthropic API."""
    return [
        {
            "name": "fetch_results",
            "description": "Fetch growth rate results from Monomer. Returns a DataFrame summary with condition, base_media, growth_rate, max_od600 for each well.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "plate_id": {
                        "type": "string",
                        "description": "Monomer plate barcode ID (e.g. PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ)"
                    }
                },
                "required": ["plate_id"]
            }
        },
        {
            "name": "analyze_results",
            "description": "Analyze growth data: rank conditions, compute confidence intervals, compare with previous round. Returns ranked table + convergence status.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "current_round_csv": {
                        "type": "string",
                        "description": "Path to current round growth CSV"
                    },
                    "previous_best_rate": {
                        "type": "number",
                        "description": "Best growth rate from previous round (0 if first round)"
                    }
                },
                "required": ["current_round_csv"]
            }
        },
        {
            "name": "elnora_design",
            "description": "Ask Elnora AI to design next experiment conditions. Use when <8 unique conditions have been tested. Sends results summary and constraints, returns proposed conditions with biological rationale.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "results_summary": {
                        "type": "string",
                        "description": "Markdown table of current results ranked by growth rate"
                    },
                    "round_number": {
                        "type": "integer",
                        "description": "Next round number"
                    },
                    "n_conditions": {
                        "type": "integer",
                        "description": "Number of conditions to propose (default 10)"
                    },
                    "specific_question": {
                        "type": "string",
                        "description": "Specific biological question to ask Elnora"
                    }
                },
                "required": ["results_summary", "round_number"]
            }
        },
        {
            "name": "elnora_validate",
            "description": "Ask Elnora to validate proposed conditions for biological plausibility. Checks precipitation risks, osmolarity, known inhibition thresholds.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "conditions_table": {
                        "type": "string",
                        "description": "Markdown table of proposed conditions with concentrations"
                    }
                },
                "required": ["conditions_table"]
            }
        },
        {
            "name": "baybe_propose",
            "description": "Run BayBE Bayesian optimization to propose next conditions. Uses historical data to fit surrogate model and maximize expected improvement.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "n_proposals": {
                        "type": "integer",
                        "description": "Number of conditions to propose (default 10)"
                    },
                    "round_number": {
                        "type": "integer",
                        "description": "Round number for labeling"
                    }
                },
                "required": ["n_proposals"]
            }
        },
        {
            "name": "compile_protocol",
            "description": "Convert proposed conditions (final concentrations) into a transfer_array JSON for the Monomer robot. Handles g/L → µL conversion using stock concentrations.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "conditions_json": {
                        "type": "string",
                        "description": "JSON array of condition objects with base_media and component concentrations"
                    },
                    "wells": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target wells on experiment plate (e.g. ['B2','B3',...,'B11'])"
                    }
                },
                "required": ["conditions_json", "wells"]
            }
        },
        {
            "name": "monomer_submit",
            "description": "Submit a workflow to the Monomer robot. Creates workflow definition file, validates, registers, and instantiates.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "transfer_array_json": {
                        "type": "string",
                        "description": "JSON string of the transfer array"
                    },
                    "monitoring_wells": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "All wells to monitor (cumulative across rounds)"
                    },
                    "plate_barcode": {
                        "type": "string",
                        "description": "Experiment plate barcode"
                    },
                    "round_label": {
                        "type": "string",
                        "description": "Human-readable label for this round"
                    }
                },
                "required": ["transfer_array_json", "monitoring_wells", "plate_barcode"]
            }
        },
        {
            "name": "check_convergence",
            "description": "Check if optimization has converged by comparing confidence intervals between rounds.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "current_best_rate": {"type": "number"},
                    "current_best_se": {"type": "number"},
                    "previous_best_rate": {"type": "number"},
                    "previous_best_se": {"type": "number"}
                },
                "required": ["current_best_rate", "current_best_se", "previous_best_rate", "previous_best_se"]
            }
        },
        {
            "name": "check_precipitation",
            "description": "Check proposed conditions for known precipitation risks (e.g. CaCl2+K2HPO4, MgSO4+K2HPO4). Returns warnings with suggested fixes.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "conditions_json": {
                        "type": "string",
                        "description": "JSON array of condition dicts with component names as keys"
                    }
                },
                "required": ["conditions_json"]
            }
        },
    ]


def execute_tool(name: str, input_data: dict) -> str:
    """Dispatch tool call to implementation."""
    from tools.analyzer import analyze_results
    from tools.baybe_tools import baybe_propose
    from tools.compiler import compile_protocol
    from tools.elnora_client import elnora_design, elnora_validate
    from tools.monomer_client import fetch_results, monomer_submit
    from tools.validators import check_convergence, check_precipitation

    auto_approve = os.environ.get("AUTO_APPROVE", "0") == "1"

    # Human checkpoint before robot submission
    if name == "monomer_submit":
        print(f"\n⚠️  ROBOT SUBMISSION REQUESTED")
        print(f"  Plate: {input_data.get('plate_barcode')}")
        print(f"  Round: {input_data.get('round_label')}")
        print(f"  Wells: {input_data.get('monitoring_wells')}")
        if not auto_approve:
            confirm = input("  Approve? [y/N]: ").strip().lower()
            if confirm != "y":
                return json.dumps({"error": "User rejected robot submission"})
        else:
            print("  Auto-approved.")

    if name == "compile_protocol":
        print(f"\n⚠️  COMPILE PROTOCOL REQUESTED")
        print(f"  Wells: {input_data.get('wells')}")
        conds = input_data.get("conditions_json", "")
        if isinstance(conds, str):
            try:
                parsed = json.loads(conds)
                print(f"  Conditions: {len(parsed)} entries")
            except json.JSONDecodeError:
                print(f"  Conditions: (unparseable)")
        if not auto_approve:
            confirm = input("  Approve? [y/N]: ").strip().lower()
            if confirm != "y":
                return json.dumps({"error": "User rejected protocol compilation"})
        else:
            print("  Auto-approved.")

    # Fix #6: check_precipitation tool dispatch
    if name == "check_precipitation":
        conditions = json.loads(input_data["conditions_json"])
        result = check_precipitation(conditions)
        return json.dumps(result, default=str)

    dispatch = {
        "fetch_results": fetch_results,
        "analyze_results": analyze_results,
        "elnora_design": elnora_design,
        "elnora_validate": elnora_validate,
        "baybe_propose": baybe_propose,
        "compile_protocol": compile_protocol,
        "monomer_submit": monomer_submit,
        "check_convergence": check_convergence,
    }

    fn = dispatch.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = fn(**input_data)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_loop(initial_plate_id: str | None = None, resume: bool = False) -> None:
    """Main orchestration loop."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    tools = get_tools()

    messages = []
    round_info: dict = {}

    # Fix #2: Resume from saved state
    if resume:
        state = load_state()
        if state:
            messages = state["messages"]
            round_info = state.get("round_info", {})
            print(f"Resumed from state saved at {state.get('timestamp')}")
            print(f"  Messages: {len(messages)}, Round info: {round_info}")
        else:
            print("No saved state found, starting fresh.")

    if not messages:
        # Seed with initial context
        if initial_plate_id:
            user_msg = (
                f"Round 1 results are available. Plate ID: {initial_plate_id}. "
                f"Fetch the results, analyze them, and propose the next round of conditions. "
                f"We have 10 wells available (B2-B11), 3 reps + 1 blank per condition."
            )
        else:
            user_msg = (
                "No previous results. Design an initial screening experiment. "
                "Use elnora_design to propose 10 conditions for V. natriegens "
                "media optimization across multiple base media types."
            )

        messages.append({"role": "user", "content": user_msg})
        save_state(messages, round_info)

    max_iterations = 50  # safety limit on tool-use turns
    for i in range(max_iterations):
        # Fix #4: Trim context before API call
        trimmed = trim_messages(messages)

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=trimmed,
        )

        # Collect assistant response
        messages.append({"role": "assistant", "content": response.content})
        save_state(messages, round_info)

        # Check if done
        if response.stop_reason == "end_turn":
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\n{'='*60}")
                    print("ORCHESTRATOR DECISION:")
                    print(block.text)
                    print(f"{'='*60}")
            break

        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [Tool] {block.name}({json.dumps(block.input)[:100]}...)")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            save_state(messages, round_info)

    print("\nOrchestrator loop complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Closed-loop media optimization orchestrator")
    parser.add_argument("--plate-id", default=None, help="Initial plate ID to fetch results from")
    parser.add_argument("--resume", action="store_true", help="Resume from saved state")
    parser.add_argument("--auto-approve", action="store_true", help="Skip human checkpoints (auto-approve all)")
    args = parser.parse_args()
    if args.auto_approve:
        os.environ["AUTO_APPROVE"] = "1"
    run_loop(initial_plate_id=args.plate_id, resume=args.resume)
