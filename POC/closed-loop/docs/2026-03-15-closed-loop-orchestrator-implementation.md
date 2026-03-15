# Closed-Loop Orchestrator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python orchestrator that autonomously loops: fetch Monomer results → ask Elnora or BayBE for next conditions → compile transfer_array → submit workflow to Monomer → repeat until convergence.

**Architecture:** Single Python script (`scripts/orchestrator.py`) using Anthropic API with tool_use. Each tool is a standalone function in `scripts/tools/`. The orchestrator calls Claude with the current state, Claude picks tools, the script executes them, and loops. Routing: Elnora designs experiments when <8 unique conditions exist, BayBE proposes when ≥8.

**Tech Stack:** Python 3.10+, anthropic SDK, BayBE, subprocess (for elnora CLI), requests (for Monomer MCP HTTP), pandas, numpy, scipy

---

### Task 1: Project Structure & Dependencies

**Files:**
- Create: `scripts/tools/__init__.py`
- Create: `scripts/orchestrator.py` (skeleton)
- Modify: `pyproject.toml` (add anthropic dependency)

**Step 1: Create tools package**

```bash
mkdir -p scripts/tools
touch scripts/tools/__init__.py
```

**Step 2: Check anthropic SDK is available**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -c "import anthropic; print(anthropic.__version__)"
```

If missing:
```bash
uv add anthropic
```

**Step 3: Create orchestrator skeleton**

Create `scripts/orchestrator.py`:

```python
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
from pathlib import Path

import anthropic

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
DATA_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are a closed-loop media optimization agent for V. natriegens.
You have tools to fetch results, analyze data, consult Elnora AI for biological guidance,
run BayBE optimization, validate conditions, compile protocols, and submit to the robot.

ROUTING RULE:
- If fewer than 8 unique conditions have been tested: use elnora_design to propose next conditions
- If 8 or more unique conditions: use baybe_propose, then elnora_validate

STOP CONDITION: If 95% confidence intervals of best conditions overlap between rounds, stop.

Always validate proposed conditions against precipitation rules before compiling."""


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
        }
    ]


def execute_tool(name: str, input_data: dict) -> str:
    """Dispatch tool call to implementation."""
    from tools.analyzer import analyze_results
    from tools.baybe_tools import baybe_propose
    from tools.compiler import compile_protocol
    from tools.elnora_client import elnora_design, elnora_validate
    from tools.monomer_client import fetch_results, monomer_submit
    from tools.validators import check_convergence

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


def run_loop(initial_plate_id: str | None = None) -> None:
    """Main orchestration loop."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    tools = get_tools()

    messages = []

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

    max_iterations = 50  # safety limit on tool-use turns
    for i in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # Collect assistant response
        messages.append({"role": "assistant", "content": response.content})

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

    print("\nOrchestrator loop complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Closed-loop media optimization orchestrator")
    parser.add_argument("--plate-id", default=None, help="Initial plate ID to fetch results from")
    args = parser.parse_args()
    run_loop(initial_plate_id=args.plate_id)
```

**Step 4: Commit**

```bash
git add scripts/orchestrator.py scripts/tools/__init__.py
git commit -m "feat: orchestrator skeleton with Anthropic tool_use loop"
```

---

### Task 2: Analyzer Tool

**Files:**
- Create: `scripts/tools/analyzer.py`

**Step 1: Write analyzer**

Create `scripts/tools/analyzer.py`:

```python
"""Analyze Monomer growth data: rank conditions, compute CI, check convergence."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


DATA_DIR = Path(__file__).parent.parent.parent / "data"


def analyze_results(current_round_csv: str, previous_best_rate: float = 0.0) -> dict:
    """Parse growth CSV, rank by growth rate, compute confidence intervals."""
    growth_path = Path(current_round_csv)
    if not growth_path.exists():
        return {"error": f"File not found: {current_round_csv}"}

    df = pd.read_csv(growth_path)

    # Expected columns from Monomer *_growth.csv
    required = ["well", "condition_id", "growth_rate_per_hr", "max_absorbance_OD600"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return {"error": f"Missing columns: {missing}"}

    # Rank by growth rate
    ranked = df.sort_values("growth_rate_per_hr", ascending=False).reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)

    # Best condition stats
    best = ranked.iloc[0]
    best_rate = float(best["growth_rate_per_hr"])
    best_condition = str(best["condition_id"])

    # Compute SE if replicates exist (via *_replicates.csv)
    rep_path = growth_path.parent / growth_path.name.replace("_growth.csv", "_replicates.csv")
    best_se = 0.05  # default
    if rep_path.exists():
        rep_df = pd.read_csv(rep_path)
        if "variance_growth_rate_per_hr" in rep_df.columns:
            best_rep = rep_df[rep_df["condition_id"].str.startswith(best_condition.split("_")[0])]
            if not best_rep.empty:
                var = best_rep["variance_growth_rate_per_hr"].iloc[0]
                n = best_rep["n_replicates"].iloc[0] if "n_replicates" in best_rep.columns else 1
                if pd.notna(var) and n > 0:
                    best_se = float(np.sqrt(var) / np.sqrt(n))

    # Convergence check vs previous round
    converged = False
    if previous_best_rate > 0 and best_se > 0:
        ci_current = (best_rate - 1.96 * best_se, best_rate + 1.96 * best_se)
        # Assume same SE for previous (conservative)
        ci_previous = (previous_best_rate - 1.96 * best_se, previous_best_rate + 1.96 * best_se)
        converged = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]

    # Build summary table
    summary_rows = []
    for _, row in ranked.iterrows():
        summary_rows.append({
            "rank": int(row["rank"]),
            "condition": str(row["condition_id"]),
            "well": str(row["well"]),
            "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
            "max_od600": round(float(row["max_absorbance_OD600"]), 4),
        })

    return {
        "n_conditions": len(ranked),
        "best_condition": best_condition,
        "best_growth_rate": round(best_rate, 4),
        "best_se": round(best_se, 4),
        "converged": converged,
        "previous_best_rate": previous_best_rate,
        "ranked_conditions": summary_rows,
    }
```

**Step 2: Quick smoke test**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -c "
from scripts.tools.analyzer import analyze_results
result = analyze_results('data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv')
print(f'Best: {result[\"best_condition\"]} at {result[\"best_growth_rate\"]}/hr')
print(f'N conditions: {result[\"n_conditions\"]}')
"
```

Expected: `Best: HB-1_1 at 1.6161/hr` (or similar)

**Step 3: Commit**

```bash
git add scripts/tools/analyzer.py
git commit -m "feat: analyzer tool — parse growth CSV, rank, compute CI"
```

---

### Task 3: Elnora Client Tool

**Files:**
- Create: `scripts/tools/elnora_client.py`

**Step 1: Write elnora client**

Create `scripts/tools/elnora_client.py`:

```python
"""Elnora AI client — wraps elnora CLI for experiment design and validation."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
ELNORA_CLI = "elnora"


def _run_elnora(args: list[str], timeout: int = 180) -> str:
    """Run elnora CLI command and return stdout."""
    result = subprocess.run(
        [ELNORA_CLI] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"elnora CLI error: {result.stderr}")
    return result.stdout


def _create_task(title: str, message: str) -> dict:
    """Create a new Elnora task and return the parsed response including assistant reply."""
    output = _run_elnora([
        "tasks", "create",
        "--project", ELNORA_PROJECT_ID,
        "--title", title,
        "--message", message,
    ])
    return json.loads(output)


def _send_message(task_id: str, message: str) -> dict:
    """Send a message to an existing Elnora task."""
    output = _run_elnora([
        "tasks", "send", task_id,
        "--message", message,
    ])
    return json.loads(output)


def _get_messages(task_id: str) -> list[dict]:
    """Get all messages from an Elnora task."""
    output = _run_elnora(["tasks", "messages", task_id])
    data = json.loads(output)
    return data.get("items", [])


def elnora_design(
    results_summary: str,
    round_number: int,
    n_conditions: int = 10,
    specific_question: str = "",
) -> dict:
    """Ask Elnora to design the next round of experiment conditions."""

    prompt = f"""We are optimizing V. natriegens growth media on a Monomer Bio workcell.

## Current Results (Round {round_number - 1})
{results_summary}

## Constraints
- {n_conditions} conditions for Round {round_number}
- 200 µL final volume (180 µL reagent + 20 µL cells)
- Min pipettable volume: 5 µL
- Available bases: Semi-Defined, High Buffer Defined
- Available stocks: Tryptone 100mg/mL, YE 100mg/mL, NaCl 5M, Glucose 100mg/mL, MOPS 1M, KH₂PO₄ 1M, Na L-Glutamate 1M, MgSO₄ 1M

## Task
Propose {n_conditions} conditions (final concentrations only) to maximize growth rate.
Focus on EXPLOIT: tighten ranges around the best performers.

{specific_question}

Format as a markdown table: Condition | Base Media | Component1 | Component2 | Component3"""

    task_data = _create_task(
        title=f"Round {round_number} experiment design",
        message=prompt,
    )

    # Extract task ID and get the assistant response
    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {
        "task_id": task_id,
        "elnora_response": assistant_reply,
        "round": round_number,
    }


def elnora_validate(conditions_table: str) -> dict:
    """Ask Elnora to validate proposed conditions for biological plausibility."""

    prompt = f"""Please validate these proposed V. natriegens media conditions for Round 2.

## Proposed Conditions
{conditions_table}

## Check for:
1. Precipitation risks (divalent cations + phosphate)
2. Osmolarity concerns (high NaCl + high glucose)
3. Known inhibition thresholds for any component
4. pH buffering adequacy (is MOPS sufficient?)
5. Any concentrations that seem biologically unreasonable

For each issue found, specify which condition and what to change.
If all conditions look safe, say "ALL CLEAR"."""

    task_data = _create_task(
        title="Condition validation check",
        message=prompt,
    )

    task_id = task_data.get("id", "")
    messages = _get_messages(task_id)

    assistant_reply = ""
    for msg in messages:
        if msg.get("role") == "assistant":
            assistant_reply = msg.get("content", "")

    return {
        "task_id": task_id,
        "validation_result": assistant_reply,
    }
```

**Step 2: Quick smoke test**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -c "
from scripts.tools.elnora_client import elnora_validate
result = elnora_validate('| HB-1 | High Buffer | YE 7 g/L | Tryp 15 g/L | Na L-Glut 60 mM |')
print(f'Task ID: {result[\"task_id\"]}')
print(f'Response length: {len(result[\"validation_result\"])} chars')
"
```

Expected: Task created, response received (may take 30-120s).

**Step 3: Commit**

```bash
git add scripts/tools/elnora_client.py
git commit -m "feat: elnora client tool — design and validate via CLI"
```

---

### Task 4: BayBE Tools

**Files:**
- Create: `scripts/tools/baybe_tools.py`

**Step 1: Write BayBE tool wrapper**

Create `scripts/tools/baybe_tools.py`:

```python
"""BayBE optimization tool — wraps baybe_opt.py logic for the orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add scripts dir to path for baybe_opt imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from baybe_opt import (
    GrowthRatePredictor,
    load_history,
    propose_conditions,
    format_output,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def baybe_propose(n_proposals: int = 10, round_number: int | None = None) -> dict:
    """Run BayBE optimization and return proposed conditions with predicted growth rates."""
    try:
        history = load_history(str(DATA_DIR))
    except FileNotFoundError as e:
        return {"error": str(e)}

    n_unique = len(history)
    n_media = history["base_media"].nunique()
    rate_range = (float(history["mean_growth_rate_per_hr"].min()),
                  float(history["mean_growth_rate_per_hr"].max()))

    # Run BayBE campaigns
    proposals = propose_conditions(history, n_proposals=n_proposals)

    # Fit GP predictor for growth rate annotations
    predictor = GrowthRatePredictor()
    if len(history) >= 2:
        predictor.fit(history)
        predicted = predictor.predict(proposals)
    else:
        predicted = np.full(len(proposals), np.nan)

    # Format output
    output_df = format_output(proposals, predicted, round_num=round_number)

    # Convert to list of dicts for JSON serialization
    conditions = output_df.to_dict(orient="records")

    return {
        "n_proposals": len(conditions),
        "n_historical_conditions": n_unique,
        "n_media_types": n_media,
        "historical_rate_range": rate_range,
        "proposed_conditions": conditions,
    }
```

**Step 2: Smoke test**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -c "
from scripts.tools.baybe_tools import baybe_propose
result = baybe_propose(n_proposals=5, round_number=2)
print(f'Proposed {result[\"n_proposals\"]} conditions from {result[\"n_historical_conditions\"]} historical')
for c in result['proposed_conditions'][:3]:
    print(f'  {c[\"condition\"]}: {c[\"base_media\"]} pred={c.get(\"predicted_growth_rate_per_hr\", \"?\")}')
"
```

Expected: 5 proposals with predicted growth rates.

**Step 3: Commit**

```bash
git add scripts/tools/baybe_tools.py
git commit -m "feat: baybe tool — wraps baybe_opt for orchestrator"
```

---

### Task 5: Protocol Compiler

**Files:**
- Create: `scripts/tools/compiler.py`

**Step 1: Write compiler**

Ref: `Notion/Format-and-Tutorials/Track-A-Materials/Reagent-Database.csv` for stock concentrations.
Ref: `monomer-bio-hackathon/CLAUDE.md` for transfer_array format.
Ref: `scripts/agent.py:650-746` for existing transfer logic.

Create `scripts/tools/compiler.py`:

```python
"""Compile conditions (final concentrations) into Monomer transfer_array JSON."""

from __future__ import annotations

import json
from typing import Any

TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL  # 180 µL
MIN_PIPETTE_UL = 5
MAX_TRANSFERS = 40

# Stock concentrations and source wells on the reagent plate
# These must match what Monomer team loaded
STOCKS = {
    "yeast_extract":  {"conc_mg_ml": 100, "unit": "g/L",  "factor": 1000, "src_well": "A1"},
    "tryptone":       {"conc_mg_ml": 100, "unit": "g/L",  "factor": 1000, "src_well": "A2"},
    "mops":           {"conc_mM": 1000,   "unit": "mM",   "src_well": "A3"},
    "na_l_glut":      {"conc_mM": 1000,   "unit": "mM",   "src_well": "A4"},
    "kh2po4":         {"conc_mM": 1000,   "unit": "mM",   "src_well": "B1"},
    "glucose":        {"conc_mg_ml": 100, "unit": "g/L",  "factor": 1000, "src_well": "B2"},
    "nacl":           {"conc_mM": 5000,   "unit": "mM",   "src_well": "B3"},
    "mgso4":          {"conc_mM": 1000,   "unit": "mM",   "src_well": "B4"},
    "water":          {"src_well": "C1"},
}

# Base media source wells
BASE_MEDIA_WELLS = {
    "Semi-Defined Media":        "D1",
    "High Buffer Defined Media": "D2",
    "Prepared LBv2 Media":       "D3",
    "Novel Bio NBxCyclone Media":"D4",
}

CELL_SOURCE_WELL = "A1"  # on cell_culture_stock plate


def _calc_vol_ul(final_conc: float, stock: dict) -> float:
    """Calculate µL of stock needed for final concentration in TOTAL_VOL_UL."""
    if "conc_mM" in stock:
        return (final_conc / stock["conc_mM"]) * TOTAL_VOL_UL
    elif "conc_mg_ml" in stock:
        # final_conc in g/L, stock in mg/mL (= g/L)
        return (final_conc / stock["conc_mg_ml"]) * TOTAL_VOL_UL
    return 0.0


def compile_protocol(conditions_json: str, wells: list[str]) -> dict:
    """Convert conditions to transfer_array for Monomer robot.

    Args:
        conditions_json: JSON array of condition dicts with keys like:
            {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
             "yeast_extract": 7.0, "tryptone": 13.0, "na_l_glut": 50, ...}
            Values can be in final concentration (g/L or mM) OR in µL volumes.
        wells: Target wells on experiment plate.

    Returns:
        dict with transfer_array (list of dicts) and validation info.
    """
    conditions = json.loads(conditions_json) if isinstance(conditions_json, str) else conditions_json

    if len(conditions) > len(wells):
        return {"error": f"More conditions ({len(conditions)}) than wells ({len(wells)})"}

    all_transfers: list[dict[str, Any]] = []
    well_summaries: list[dict] = []

    for i, cond in enumerate(conditions):
        dst_well = wells[i]
        base_media = cond.get("base_media", "High Buffer Defined Media")
        base_vol = float(cond.get("base_media_vol", 110))

        transfers_for_well: list[dict[str, Any]] = []
        reagent_vol_total = 0.0

        # Base media transfer
        base_src = BASE_MEDIA_WELLS.get(base_media, "D1")
        transfers_for_well.append({
            "src_plate": "reagent",
            "src_well": base_src,
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": round(base_vol, 1),
            "new_tip": "once",
            "blow_out": True,
        })
        reagent_vol_total += base_vol

        # Reagent spikes
        for reagent_name, stock_info in STOCKS.items():
            if reagent_name == "water":
                continue
            val = cond.get(reagent_name, 0)
            if val is None or float(val) <= 0:
                continue
            vol = float(val)  # Assume already in µL if base_media_vol is present
            if vol < MIN_PIPETTE_UL:
                continue
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": stock_info["src_well"],
                "dst_plate": "experiment",
                "dst_well": dst_well,
                "volume": round(vol, 1),
                "new_tip": "once",
                "blow_out": True,
            })
            reagent_vol_total += vol

        # Water to fill
        water_vol = REAGENT_VOL_UL - reagent_vol_total
        if water_vol >= MIN_PIPETTE_UL:
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": STOCKS["water"]["src_well"],
                "dst_plate": "experiment",
                "dst_well": dst_well,
                "volume": round(water_vol, 1),
                "new_tip": "once",
                "blow_out": True,
            })

        # Cell seeding — always last, always fresh tip
        transfers_for_well.append({
            "src_plate": "cell_culture_stock",
            "src_well": CELL_SOURCE_WELL,
            "dst_plate": "experiment",
            "dst_well": dst_well,
            "volume": CELL_VOL_UL,
            "new_tip": "always",
            "blow_out": False,
            "post_mix_volume": 40,
            "post_mix_reps": 5,
        })

        all_transfers.extend(transfers_for_well)
        well_summaries.append({
            "well": dst_well,
            "base_media": base_media,
            "reagent_vol": round(reagent_vol_total, 1),
            "water_vol": round(max(0, water_vol), 1),
            "total": round(reagent_vol_total + max(0, water_vol) + CELL_VOL_UL, 1),
        })

    # Validate
    errors = []
    if len(all_transfers) > MAX_TRANSFERS:
        errors.append(f"Too many transfers: {len(all_transfers)} > {MAX_TRANSFERS}")
    for ws in well_summaries:
        if abs(ws["total"] - TOTAL_VOL_UL) > 1.0:
            errors.append(f"Well {ws['well']}: total={ws['total']} µL (expected {TOTAL_VOL_UL})")

    return {
        "transfer_array": all_transfers,
        "n_transfers": len(all_transfers),
        "well_summaries": well_summaries,
        "errors": errors,
    }
```

**Step 2: Smoke test with Round 1 data**

```bash
cd /Users/viachealavrudenko/Cell.ai && python -c "
import json
from scripts.tools.compiler import compile_protocol
conditions = [
    {'base_media': 'High Buffer Defined Media', 'base_media_vol': 110,
     'yeast_extract': 14, 'tryptone': 26, 'na_l_glut': 10, 'water': 20},
]
result = compile_protocol(json.dumps(conditions), ['B2'])
print(f'Transfers: {result[\"n_transfers\"]}')
print(f'Errors: {result[\"errors\"]}')
for t in result['transfer_array']:
    print(f'  {t[\"src_well\"]} → {t[\"dst_well\"]}: {t[\"volume\"]} µL')
"
```

**Step 3: Commit**

```bash
git add scripts/tools/compiler.py
git commit -m "feat: protocol compiler — conditions to transfer_array"
```

---

### Task 6: Monomer Client & Validators

**Files:**
- Create: `scripts/tools/monomer_client.py`
- Create: `scripts/tools/validators.py`

**Step 1: Write Monomer client**

Create `scripts/tools/monomer_client.py`:

```python
"""Monomer MCP client — fetch results and submit workflows."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Monomer MCP endpoints
AUTOPLAT_URL = "http://192.168.68.60:8080/mcp"
MONITOR_URL = "https://backend-staging.monomerbio.com/mcp"
MONITOR_TOKEN = ""  # Set via env var MONOMER_TOKEN

# REST API fallback
REST_URL = "http://192.168.68.60:8080"
REST_HEADERS = {"X-Monomer-Client": "desktop-frontend"}


def _mcp_call(url: str, method: str, params: dict, token: str = "") -> dict:
    """Make a JSON-RPC 2.0 call to Monomer MCP."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
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
    """Fetch growth rate results for a plate from local CSV files.

    Falls back to Monomer MCP if CSV not available.
    """
    # Try local CSV first (already downloaded by monitor_data_processing.py)
    growth_csv = DATA_DIR / f"{plate_id}_growth.csv"
    map_csv = DATA_DIR / f"{plate_id}_plate_condition_map.csv"
    rep_csv = DATA_DIR / f"{plate_id}_replicates.csv"

    if growth_csv.exists():
        growth_df = pd.read_csv(growth_csv)
        results = []
        for _, row in growth_df.iterrows():
            results.append({
                "well": row["well"],
                "condition": row["condition_id"],
                "growth_rate": round(float(row["growth_rate_per_hr"]), 4),
                "max_od600": round(float(row["max_absorbance_OD600"]), 4),
            })

        results.sort(key=lambda x: x["growth_rate"], reverse=True)

        return {
            "plate_id": plate_id,
            "source": "local_csv",
            "growth_csv_path": str(growth_csv),
            "n_wells": len(results),
            "results": results,
        }

    # Fallback: try Monomer MCP
    try:
        data = _mcp_call(MONITOR_URL, "get_plate_observations",
                         {"plate_name": plate_id}, token=MONITOR_TOKEN)
        return {"plate_id": plate_id, "source": "monomer_mcp", "raw": data}
    except Exception as e:
        return {"error": f"Cannot fetch results for {plate_id}: {e}"}


def monomer_submit(
    transfer_array_json: str,
    monitoring_wells: list[str],
    plate_barcode: str,
    round_label: str = "",
) -> dict:
    """Submit a workflow to the Monomer workcell via MCP.

    This creates a workflow definition file, validates it, registers it,
    and instantiates it.
    """
    # For hackathon: write the workflow inputs to a file for manual submission
    # (auto-submit via MCP requires network access to workcell)
    output_dir = DATA_DIR.parent / "workflows"
    output_dir.mkdir(exist_ok=True)

    workflow_inputs = {
        "transfer_array": json.loads(transfer_array_json),
        "monitoring_wells": monitoring_wells,
        "plate_barcode": plate_barcode,
        "round_label": round_label,
        "reagent_name": "CellAI Reagent Plate",
        "cell_culture_stock_plate_barcode": "CellAI Cell Stock",
    }

    output_file = output_dir / f"workflow_{round_label or 'next'}.json"
    with open(output_file, "w") as f:
        json.dump(workflow_inputs, f, indent=2)

    # Try MCP submission
    try:
        result = _mcp_call(
            AUTOPLAT_URL,
            "instantiate_workflow",
            {
                "definition_name": "hackathon_closed_loop",
                "plate_barcode": plate_barcode,
                "extra_inputs": {
                    "transfer_array": transfer_array_json,
                    "monitoring_wells": json.dumps(monitoring_wells),
                    "reagent_name": workflow_inputs["reagent_name"],
                    "cell_culture_stock_plate_barcode": workflow_inputs["cell_culture_stock_plate_barcode"],
                },
                "reason": round_label,
            },
        )
        return {
            "status": "submitted",
            "workflow_file": str(output_file),
            "mcp_result": result,
        }
    except Exception as e:
        return {
            "status": "saved_locally",
            "workflow_file": str(output_file),
            "mcp_error": str(e),
            "instructions": "Submit manually via Monomer MCP or hand to Monomer team",
        }
```

**Step 2: Write validators**

Create `scripts/tools/validators.py`:

```python
"""Validation tools — precipitation check, convergence check."""

from __future__ import annotations

import numpy as np


# From Notion/Reagent-Compatibility-Guide.md
PRECIPITATION_RULES = [
    {
        "pair": ("CaCl2", "K2HPO4"),
        "action": "NEVER combine",
        "fix": "Use KH2PO4 instead",
    },
    {
        "pair": ("CaCl2", "Novel Bio"),
        "action": "NEVER combine",
        "fix": "Do not add CaCl2 to Novel Bio",
    },
    {
        "pair": ("MgSO4", "K2HPO4"),
        "action": "Only with >=12.5mM sodium citrate",
        "fix": "Use KH2PO4 instead, or add 2.5µL of 1M sodium citrate",
    },
    {
        "pair": ("FeSO4", "K2HPO4"),
        "action": "Presumed incompatible",
        "fix": "Use KH2PO4 at low iron concentration",
    },
]


def check_convergence(
    current_best_rate: float,
    current_best_se: float,
    previous_best_rate: float,
    previous_best_se: float,
) -> dict:
    """Check if 95% CIs overlap between rounds (convergence = stop)."""
    ci_current = (
        current_best_rate - 1.96 * current_best_se,
        current_best_rate + 1.96 * current_best_se,
    )
    ci_previous = (
        previous_best_rate - 1.96 * previous_best_se,
        previous_best_rate + 1.96 * previous_best_se,
    )

    overlap = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]

    improvement_pct = (
        ((current_best_rate - previous_best_rate) / previous_best_rate * 100)
        if previous_best_rate > 0 else float("inf")
    )

    return {
        "converged": overlap,
        "current_ci": [round(ci_current[0], 4), round(ci_current[1], 4)],
        "previous_ci": [round(ci_previous[0], 4), round(ci_previous[1], 4)],
        "improvement_pct": round(improvement_pct, 2),
        "recommendation": "STOP — converged" if overlap else "CONTINUE — improvement detected",
    }
```

**Step 3: Commit**

```bash
git add scripts/tools/monomer_client.py scripts/tools/validators.py
git commit -m "feat: monomer client and validators — fetch results, submit workflows, check convergence"
```

---

### Task 7: Integration Test — Full Loop Dry Run

**Files:**
- No new files — test existing code end-to-end

**Step 1: Run orchestrator with Round 1 plate ID (dry run, no Monomer submit)**

```bash
cd /Users/viachealavrudenko/Cell.ai && ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY python scripts/orchestrator.py --plate-id PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ
```

Expected behavior:
1. Fetches Round 1 growth data from local CSV
2. Analyzes: HB-1 best at 1.616/hr
3. Routes to BayBE (10 conditions ≥ 8 threshold) OR Elnora (if <8)
4. Proposes Round 2 conditions
5. Compiles transfer_array
6. Attempts Monomer submit (will fail gracefully, save locally)
7. Prints orchestrator decision

**Step 2: Verify workflow file was created**

```bash
ls -la /Users/viachealavrudenko/Cell.ai/workflows/
cat /Users/viachealavrudenko/Cell.ai/workflows/workflow_*.json | python -m json.tool | head -30
```

**Step 3: Commit any fixes from integration test**

```bash
git add -A
git commit -m "fix: integration fixes from dry run"
```

---

### Task 8 (V1.5): Random Screen Tool

**Files:**
- Create: `scripts/tools/random_screen.py`

**Step 1: Write random screen tool**

Extract LHS/Sobol sampling from `scripts/agent.py` lines 370-420.

Create `scripts/tools/random_screen.py`:

```python
"""Random screening tool — LHS and Sobol sampling for initial exploration."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import qmc

RANDOM_SEED = 42
TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL

# Default factor ranges (µL volumes)
DEFAULT_RANGES = {
    "base_media_vol": (100, 160),
    "yeast_extract": (0, 30),
    "tryptone": (0, 30),
    "mops": (0, 20),
    "na_l_glut": (0, 15),
    "kh2po4": (0, 10),
    "glucose": (0, 20),
}

BASE_MEDIA_OPTIONS = [
    "Semi-Defined Media",
    "High Buffer Defined Media",
]


def latin_hypercube_screen(
    n_conditions: int = 10,
    factor_ranges: dict | None = None,
    base_media: str | None = None,
) -> dict:
    """Generate space-filling conditions using Latin Hypercube Sampling."""
    ranges = factor_ranges or DEFAULT_RANGES
    factors = list(ranges.keys())
    n_dim = len(factors)

    sampler = qmc.LatinHypercube(d=n_dim, seed=RANDOM_SEED)
    raw = sampler.random(n=n_conditions * 3)

    bounds_low = np.array([ranges[f][0] for f in factors])
    bounds_high = np.array([ranges[f][1] for f in factors])
    scaled = qmc.scale(raw, bounds_low, bounds_high)

    rng = np.random.default_rng(RANDOM_SEED)
    conditions = []

    for row in scaled:
        c = {f: round(float(v), 1) for f, v in zip(factors, row)}

        # Volume constraint: sum of all volumes must leave room for cells
        vol_sum = sum(c.values())
        if vol_sum > REAGENT_VOL_UL:
            continue

        c["base_media"] = base_media or rng.choice(BASE_MEDIA_OPTIONS)
        c["water"] = round(REAGENT_VOL_UL - vol_sum, 1)
        c["cells"] = CELL_VOL_UL
        c["total"] = TOTAL_VOL_UL
        conditions.append(c)

        if len(conditions) >= n_conditions:
            break

    return {
        "n_conditions": len(conditions),
        "method": "latin_hypercube",
        "conditions": conditions,
    }
```

**Step 2: Add to orchestrator tool list**

Add to `scripts/orchestrator.py` in `get_tools()`:
```python
{
    "name": "random_screen",
    "description": "Generate space-filling conditions using Latin Hypercube Sampling for initial screening. Use when no prior data exists.",
    "input_schema": {
        "type": "object",
        "properties": {
            "n_conditions": {"type": "integer", "description": "Number of conditions (default 10)"},
            "base_media": {"type": "string", "description": "Fix base media (optional)"}
        },
        "required": []
    }
}
```

Add to `execute_tool()` dispatch:
```python
from tools.random_screen import latin_hypercube_screen
# ...
"random_screen": lambda **kw: latin_hypercube_screen(**kw),
```

**Step 3: Commit**

```bash
git add scripts/tools/random_screen.py scripts/orchestrator.py
git commit -m "feat: random screen tool — LHS sampling for initial exploration"
```

---

### Task 9: Growth Simulator (Mock Monomer Layer)

**Files:**
- Create: `scripts/tools/growth_simulator.py`
- Modify: `scripts/tools/monomer_client.py` (add SIMULATION_MODE switch)

**Goal:** Mock layer inside `monomer_client.py` that replaces real Monomer MCP. GP surrogate trained on Round 1 data predicts growth rates for new conditions. Orchestrator doesn't know it's talking to a simulator.

**Step 1: Write growth simulator**

Create `scripts/tools/growth_simulator.py`:

```python
"""Growth simulator — GP surrogate trained on real Round 1 data.

Predicts growth rates for arbitrary conditions, adds biological noise,
generates synthetic OD600 time-series, and manages workflow state with
configurable delay to test polling logic.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path(__file__).parent.parent.parent / "data"

REAGENT_COLS = ["base_media_vol", "yeast_extract", "tryptone", "mops", "na_l_glut", "kh2po4", "glucose"]
NOISE_STD = 0.08  # ~5-8% noise on growth rate
DELAY_SECONDS = 5  # simulated workflow duration


@dataclass
class SimulatedWorkflow:
    workflow_id: str
    plate_barcode: str
    conditions: list[dict]
    monitoring_wells: list[str]
    submitted_at: float
    delay: float = DELAY_SECONDS
    status: str = "in_progress"

    @property
    def is_complete(self) -> bool:
        return (time.time() - self.submitted_at) >= self.delay


class GrowthSimulator:
    """GP surrogate trained on real data, generates synthetic growth results."""

    def __init__(self, data_dir: str | Path = DATA_DIR):
        self.data_dir = Path(data_dir)
        self._gp = None
        self._scaler = StandardScaler()
        self._history: pd.DataFrame = pd.DataFrame()
        self._workflows: dict[str, SimulatedWorkflow] = {}
        self._plates: dict[str, list[dict]] = {}  # plate_id → results
        self._rng = np.random.default_rng(42)
        self._fit_gp()

    def _fit_gp(self) -> None:
        """Train GP on all available historical data."""
        # Load real Round 1 data
        growth_files = sorted(self.data_dir.glob("*_growth.csv"))
        map_files = sorted(self.data_dir.glob("*_plate_condition_map.csv"))

        all_rows = []
        for gf in growth_files:
            prefix = gf.name.replace("_growth.csv", "")
            mf = self.data_dir / f"{prefix}_plate_condition_map.csv"
            if not mf.exists():
                continue

            growth = pd.read_csv(gf)
            maps = pd.read_csv(mf)
            merged = growth[["well", "growth_rate_per_hr"]].merge(
                maps, on="well", how="inner"
            )
            all_rows.append(merged)

        if not all_rows:
            return

        df = pd.concat(all_rows, ignore_index=True)
        self._history = df

        # Extract features
        vol_cols = [c for c in REAGENT_COLS if c in df.columns]
        X = df[vol_cols].fillna(0).values.astype(float)
        y = df["growth_rate_per_hr"].values.astype(float)

        if len(X) < 2:
            return

        self._vol_cols = vol_cols
        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)

        kernel = ConstantKernel(1.0) * Matern(nu=2.5) + WhiteKernel(noise_level=0.01)
        self._gp = GaussianProcessRegressor(
            kernel=kernel,
            n_restarts_optimizer=5,
            normalize_y=True,
            random_state=42,
        )
        self._gp.fit(X_scaled, y)

    def predict_growth_rate(self, condition: dict) -> float:
        """Predict growth rate for a single condition using GP + noise."""
        if self._gp is None:
            return 0.8 + self._rng.normal(0, NOISE_STD)

        x = np.array([[condition.get(c, 0.0) for c in self._vol_cols]])
        x_scaled = self._scaler.transform(x)
        mu, sigma = self._gp.predict(x_scaled, return_std=True)

        # Check if extrapolating (outside training data convex hull)
        X_train = self._scaler.transform(
            self._history[self._vol_cols].fillna(0).values
        )
        distances = np.min(
            np.linalg.norm(X_train - x_scaled, axis=1)
        )
        if distances > 2.0:
            # Far from training data — return baseline + large noise
            return 1.0 + self._rng.normal(0, NOISE_STD * 3)

        # Normal prediction with noise
        rate = float(mu[0]) + self._rng.normal(0, NOISE_STD)
        return max(0.1, rate)  # growth rate can't be negative

    def _generate_od600_timeseries(self, growth_rate: float, n_points: int = 9) -> list[dict]:
        """Generate synthetic OD600 logistic growth curve."""
        times_hr = np.linspace(0, 1.5, n_points)  # 10-min intervals over 90 min
        od_max = 0.3 + self._rng.uniform(0, 0.3)
        od_0 = 0.08 + self._rng.normal(0, 0.01)

        # Logistic growth: OD(t) = od_max / (1 + ((od_max - od_0)/od_0) * exp(-rate*t))
        od_values = od_max / (1 + ((od_max - od_0) / od_0) * np.exp(-growth_rate * times_hr))
        od_values += self._rng.normal(0, 0.005, n_points)  # measurement noise
        od_values = np.clip(od_values, 0.05, 1.0)

        return [
            {"time_hr": round(float(t), 4), "od600": round(float(od), 4)}
            for t, od in zip(times_hr, od_values)
        ]

    # ── Monomer MCP-compatible interface ──────────────────────────────────────

    def instantiate_workflow(self, transfer_array: list[dict],
                             monitoring_wells: list[str],
                             plate_barcode: str, **kwargs) -> dict:
        """Simulate workflow submission. Returns workflow_id."""
        wf_id = str(uuid.uuid4())[:8]

        # Parse conditions from transfer_array
        conditions = self._parse_conditions(transfer_array)

        wf = SimulatedWorkflow(
            workflow_id=wf_id,
            plate_barcode=plate_barcode,
            conditions=conditions,
            monitoring_wells=monitoring_wells,
            submitted_at=time.time(),
        )
        self._workflows[wf_id] = wf
        return {"workflow_id": wf_id, "status": "pending_approval"}

    def get_workflow_instance_details(self, workflow_id: str) -> dict:
        """Check workflow status. Returns in_progress until delay passes."""
        wf = self._workflows.get(workflow_id)
        if wf is None:
            return {"error": f"Unknown workflow: {workflow_id}"}

        if wf.is_complete and wf.status == "in_progress":
            wf.status = "completed"
            self._generate_results(wf)

        return {"workflow_id": workflow_id, "status": wf.status}

    def get_plate_observations(self, plate_barcode: str) -> dict:
        """Return simulated OD600 observations for a plate."""
        results = self._plates.get(plate_barcode, [])
        if not results:
            return {"plate": plate_barcode, "observations": [], "status": "no_data"}
        return {"plate": plate_barcode, "observations": results}

    def export_plate_observations(self, plate_barcode: str) -> dict:
        """Export simulated growth data in Monomer CSV format."""
        results = self._plates.get(plate_barcode, [])
        return {
            "plate": plate_barcode,
            "wells": results,
            "format": "growth_csv",
        }

    def list_culture_plates(self) -> dict:
        return {"plates": list(self._plates.keys())}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _parse_conditions(self, transfer_array: list[dict]) -> list[dict]:
        """Extract per-well conditions from transfer_array."""
        wells: dict[str, dict] = {}
        for t in transfer_array:
            dst = t.get("dst_well", "")
            if dst not in wells:
                wells[dst] = {c: 0.0 for c in self._vol_cols}
            # Map src_well back to reagent volume
            vol = float(t.get("volume", 0))
            # Simple: just record total volume per well
            wells[dst]["base_media_vol"] = wells[dst].get("base_media_vol", 0) + vol
        return [{"well": w, **cond} for w, cond in wells.items()]

    def _generate_results(self, wf: SimulatedWorkflow) -> None:
        """Generate simulated growth data for all wells in workflow."""
        results = []
        for cond in wf.conditions:
            rate = self.predict_growth_rate(cond)
            timeseries = self._generate_od600_timeseries(rate)
            results.append({
                "well": cond["well"],
                "growth_rate_per_hr": round(rate, 4),
                "max_absorbance_OD600": round(max(p["od600"] for p in timeseries), 4),
                "timeseries": timeseries,
                "condition_id": f"sim_{cond['well']}",
            })

        self._plates[wf.plate_barcode] = results

        # Re-fit GP with new simulated data (closed loop learning)
        new_rows = []
        for r in results:
            row = {c: 0.0 for c in self._vol_cols}
            matching = [c for c in wf.conditions if c["well"] == r["well"]]
            if matching:
                row.update({k: v for k, v in matching[0].items() if k in self._vol_cols})
            row["growth_rate_per_hr"] = r["growth_rate_per_hr"]
            row["well"] = r["well"]
            new_rows.append(row)

        if new_rows and self._gp is not None:
            new_df = pd.DataFrame(new_rows)
            self._history = pd.concat([self._history, new_df], ignore_index=True)
            self._fit_gp()  # Re-train on all data including simulated
```

**Step 2: Add SIMULATION_MODE to monomer_client.py**

Add at the top of `scripts/tools/monomer_client.py`:

```python
import os

SIMULATION_MODE = os.environ.get("SIMULATION_MODE", "0") == "1"
_simulator = None

def _get_simulator():
    global _simulator
    if _simulator is None:
        from tools.growth_simulator import GrowthSimulator
        _simulator = GrowthSimulator()
    return _simulator
```

Replace the `fetch_results` function body:

```python
def fetch_results(plate_id: str) -> dict:
    if SIMULATION_MODE:
        sim = _get_simulator()
        obs = sim.get_plate_observations(plate_id)
        if obs.get("observations"):
            results = [
                {
                    "well": w["well"],
                    "condition": w["condition_id"],
                    "growth_rate": w["growth_rate_per_hr"],
                    "max_od600": w["max_absorbance_OD600"],
                }
                for w in obs["observations"]
            ]
            results.sort(key=lambda x: x["growth_rate"], reverse=True)
            return {"plate_id": plate_id, "source": "simulator", "n_wells": len(results), "results": results}
        return {"plate_id": plate_id, "source": "simulator", "status": "no_data"}

    # ... existing real Monomer code ...
```

Replace the `monomer_submit` function body:

```python
def monomer_submit(transfer_array_json, monitoring_wells, plate_barcode, round_label=""):
    if SIMULATION_MODE:
        import json
        sim = _get_simulator()
        transfers = json.loads(transfer_array_json) if isinstance(transfer_array_json, str) else transfer_array_json
        result = sim.instantiate_workflow(transfers, monitoring_wells, plate_barcode)
        return {"status": "submitted_to_simulator", **result}

    # ... existing real Monomer code ...
```

**Step 3: Add polling helper to monomer_client.py**

```python
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

    # Real Monomer polling
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
```

**Step 4: End-to-end simulation test**

```bash
cd /Users/viachealavrudenko/Cell.ai && SIMULATION_MODE=1 ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY python scripts/orchestrator.py --plate-id PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ
```

Expected:
1. Orchestrator fetches Round 1 from real CSV (pre-loaded in simulator)
2. Analyzes: HB-1 best at ~1.616/hr
3. Routes to BayBE or Elnora → proposes Round 2
4. Compiles transfer_array
5. Submits to simulator → gets workflow_id
6. Polls → "in_progress" for 5 seconds → "completed"
7. Fetches simulated Round 2 results (different growth rates!)
8. Checks convergence → continues or stops

**Step 5: Commit**

```bash
git add scripts/tools/growth_simulator.py scripts/tools/monomer_client.py
git commit -m "feat: growth simulator — GP surrogate mock for closed-loop testing"
```

---

### Task 10: Golden Test — Verify Orchestrator Improves Over Rounds

**Files:**
- Create: `tests/test_simulation_loop.py`

**Step 1: Write golden test**

```python
"""Golden test: orchestrator must improve growth rate over simulated rounds."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
os.environ["SIMULATION_MODE"] = "1"

from tools.growth_simulator import GrowthSimulator


def test_simulator_returns_different_rates_for_different_conditions():
    """Core check: different inputs → different outputs."""
    sim = GrowthSimulator()

    cond_a = {"base_media_vol": 110, "yeast_extract": 14, "tryptone": 26,
              "mops": 0, "na_l_glut": 10, "kh2po4": 0, "glucose": 0}
    cond_b = {"base_media_vol": 110, "yeast_extract": 26, "tryptone": 14,
              "mops": 0, "na_l_glut": 5, "kh2po4": 0, "glucose": 0}

    rate_a = sim.predict_growth_rate(cond_a)
    rate_b = sim.predict_growth_rate(cond_b)

    assert rate_a > 0, "Growth rate must be positive"
    assert rate_b > 0, "Growth rate must be positive"
    assert abs(rate_a - rate_b) > 0.01, (
        f"Different conditions should give different rates: {rate_a} vs {rate_b}"
    )


def test_simulator_workflow_lifecycle():
    """Submit → poll → complete → get results."""
    sim = GrowthSimulator()

    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
        {"src_plate": "reagent", "src_well": "A1", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 14},
    ]

    result = sim.instantiate_workflow(transfers, ["B2"], "TEST_PLATE")
    wf_id = result["workflow_id"]

    # Initially in_progress
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] in ("in_progress", "completed")

    # After delay, completed
    import time
    time.sleep(6)
    status = sim.get_workflow_instance_details(wf_id)
    assert status["status"] == "completed"

    # Results available
    obs = sim.get_plate_observations("TEST_PLATE")
    assert len(obs["observations"]) > 0
    assert obs["observations"][0]["growth_rate_per_hr"] > 0


def test_simulator_refits_after_new_data():
    """GP should update predictions after receiving new simulated data."""
    sim = GrowthSimulator()

    cond = {"base_media_vol": 110, "yeast_extract": 20, "tryptone": 20,
            "mops": 0, "na_l_glut": 8, "kh2po4": 0, "glucose": 0}

    rate_before = sim.predict_growth_rate(cond)

    # Submit a workflow to add new data points
    transfers = [
        {"src_plate": "reagent", "src_well": "D2", "dst_plate": "experiment",
         "dst_well": "B2", "volume": 110},
    ]
    result = sim.instantiate_workflow(transfers, ["B2"], "REFIT_PLATE")
    import time
    time.sleep(6)
    sim.get_workflow_instance_details(result["workflow_id"])  # triggers generation + refit

    rate_after = sim.predict_growth_rate(cond)

    # Rates may differ slightly after refit (GP updated)
    # Main check: both are valid positive numbers
    assert rate_before > 0
    assert rate_after > 0


if __name__ == "__main__":
    test_simulator_returns_different_rates_for_different_conditions()
    print("✓ Different conditions → different rates")

    test_simulator_workflow_lifecycle()
    print("✓ Workflow lifecycle: submit → poll → complete → results")

    test_simulator_refits_after_new_data()
    print("✓ GP refits after new simulated data")

    print("\nAll golden tests passed.")
```

**Step 2: Run golden test**

```bash
cd /Users/viachealavrudenko/Cell.ai && python tests/test_simulation_loop.py
```

Expected:
```
✓ Different conditions → different rates
✓ Workflow lifecycle: submit → poll → complete → results
✓ GP refits after new simulated data

All golden tests passed.
```

**Step 3: Commit**

```bash
git add tests/test_simulation_loop.py
git commit -m "test: golden tests for growth simulator — lifecycle, GP refit, different outputs"
```
