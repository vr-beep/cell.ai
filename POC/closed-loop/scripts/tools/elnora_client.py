"""Elnora AI client — wraps elnora CLI for experiment design and validation."""
from __future__ import annotations

import json
import subprocess

ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
ELNORA_CLI = "elnora"


def _run_elnora(args: list[str], timeout: int = 180) -> str:
    result = subprocess.run(
        [ELNORA_CLI] + args, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"elnora CLI error: {result.stderr}")
    return result.stdout


def _create_task(title: str, message: str) -> dict:
    output = _run_elnora([
        "tasks", "create",
        "--project", ELNORA_PROJECT_ID,
        "--title", title,
        "--message", message,
    ])
    return json.loads(output)


def _send_message(task_id: str, message: str) -> dict:
    output = _run_elnora(["tasks", "send", task_id, "--message", message])
    return json.loads(output)


def _get_messages(task_id: str) -> list[dict]:
    output = _run_elnora(["tasks", "messages", task_id])
    data = json.loads(output)
    return data.get("items", [])


def elnora_design(
    results_summary: str,
    round_number: int,
    n_conditions: int = 10,
    specific_question: str = "",
) -> dict:
    prompt = f"""We are optimizing V. natriegens growth media on a Monomer Bio workcell.

## Current Results (Round {round_number - 1})
{results_summary}

## Constraints
- {n_conditions} conditions for Round {round_number}
- 200 uL final volume (180 uL reagent + 20 uL cells)
- Min pipettable volume: 5 uL
- Available bases: Semi-Defined, High Buffer Defined
- Available stocks: Tryptone 100mg/mL, YE 100mg/mL, NaCl 5M, Glucose 100mg/mL, MOPS 1M, KH2PO4 1M, Na L-Glutamate 1M, MgSO4 1M

## Task
Propose {n_conditions} conditions (final concentrations only) to maximize growth rate.
Focus on EXPLOIT: tighten ranges around the best performers.

{specific_question}

Format as a markdown table: Condition | Base Media | Component1 | Component2 | Component3"""

    task_data = _create_task(f"Round {round_number} experiment design", prompt)
    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {"task_id": task_id, "elnora_response": assistant_reply, "round": round_number}


def elnora_validate(conditions_table: str) -> dict:
    prompt = f"""Please validate these proposed V. natriegens media conditions.

## Proposed Conditions
{conditions_table}

## Check for:
1. Precipitation risks (divalent cations + phosphate)
2. Osmolarity concerns (high NaCl + high glucose)
3. Known inhibition thresholds for any component
4. pH buffering adequacy
5. Biologically unreasonable concentrations

For each issue, specify which condition and what to change.
If all safe, say "ALL CLEAR"."""

    task_data = _create_task("Condition validation check", prompt)
    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {"task_id": task_id, "validation_result": assistant_reply}
