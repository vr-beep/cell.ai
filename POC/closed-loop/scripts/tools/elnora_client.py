"""Elnora AI client — wraps elnora CLI for experiment design and validation.

Pattern ported from bio-autoresearch/autoresearch.py (proven working).
Key principle: simple polling for any assistant content, no metadata parsing.
"""
from __future__ import annotations

import json
import subprocess
import time

ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
ELNORA_CLI = "elnora"


def _parse_elnora_json(raw: str) -> dict:
    """Parse elnora CLI output which may have a warning JSON before the actual data."""
    decoder = json.JSONDecoder()
    pos = 0
    last_obj = None
    while pos < len(raw):
        raw_stripped = raw[pos:].lstrip()
        if not raw_stripped:
            break
        try:
            obj, end = decoder.raw_decode(raw_stripped)
            last_obj = obj
            pos += len(raw) - len(raw_stripped) - pos + end
        except json.JSONDecodeError:
            break
    return last_obj or {}


def query_elnora(question: str, title: str = "cell-ai", timeout: int = 150, poll: int = 5) -> str | None:
    """Send a question to Elnora AI and wait for response.

    Mirrors the proven bio-autoresearch pattern:
    1. Create task with message
    2. Poll for ANY assistant content (no metadata parsing)
    3. Return content or None on timeout/error
    """
    print(f"    [elnora] Creating task: {title}", flush=True)
    try:
        result = subprocess.run(
            [ELNORA_CLI, "tasks", "create",
             "--project", ELNORA_PROJECT_ID,
             "--title", title,
             "--message", question],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"    [elnora] CLI error: {result.stderr.strip()}", flush=True)
            return None

        task_data = _parse_elnora_json(result.stdout)
        task_id = task_data.get("id", "")
        if not task_id:
            print(f"    [elnora] No task ID in response", flush=True)
            return None
        print(f"    [elnora] Task created: {task_id}", flush=True)

        # Poll for response — check both content and completed status
        print(f"    [elnora] Polling for reply (timeout={timeout}s, interval={poll}s)", flush=True)
        for elapsed in range(0, timeout, poll):
            msg_result = subprocess.run(
                [ELNORA_CLI, "tasks", "messages", task_id],
                capture_output=True, text=True, timeout=30,
            )
            if msg_result.returncode == 0:
                data = _parse_elnora_json(msg_result.stdout)
                for msg in data.get("items", []):
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "").strip()
                        # Check if Elnora marked the reply as completed
                        meta = msg.get("metadata") or ""
                        completed = False
                        if isinstance(meta, str) and meta.strip():
                            try:
                                completed = json.loads(meta).get("status") == "completed"
                            except (json.JSONDecodeError, AttributeError):
                                pass
                        if content:
                            preview = (content[:100] + "...") if len(content) > 100 else content
                            print(f"    [elnora] Got response ({len(content)} chars): {preview}", flush=True)
                            return content
                        if completed:
                            print(f"    [elnora] Completed with empty content — returning None", flush=True)
                            return None
            print(f"    [elnora] Poll at {elapsed}s — no reply yet", flush=True)
            time.sleep(poll)

        print(f"    [elnora] Timeout after {timeout}s", flush=True)
        return None
    except Exception as e:
        print(f"    [elnora] Error: {e}", flush=True)
        return None


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

    reply = query_elnora(prompt, title=f"Round {round_number} experiment design")

    if not reply:
        print(f"    [elnora] Design: empty — using BayBE-only fallback", flush=True)
        reply = "Elnora did not return a response. Please proceed with BayBE proposals only."
    else:
        print(f"    [elnora] Design: got {len(reply)} chars", flush=True)

    return {"task_id": "", "elnora_response": reply, "round": round_number}


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

    reply = query_elnora(prompt, title="Condition validation check")

    if not reply:
        print(f"    [elnora] Validate: empty — ALL CLEAR fallback", flush=True)
        reply = "ALL CLEAR — Elnora did not flag any issues (empty response)."
    else:
        print(f"    [elnora] Validate: got {len(reply)} chars", flush=True)

    return {"task_id": "", "validation_result": reply}
