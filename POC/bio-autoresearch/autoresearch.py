"""
Bio-autoresearch: Autonomous media optimization for V. natriegens.

Inspired by Karpathy's autoresearch — an AI agent autonomously optimizes
cell culture media using scientific literature (Elnora AI) and a GP surrogate
trained on real wet-lab data from a Monomer Bio robotic workcell.

Usage: python POC/bio-autoresearch/autoresearch.py
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from simulator import evaluate_recipes, SEARCH_SPACE

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).parent.parent.parent / ".env")

RESULTS_FILE = Path(__file__).parent / "results.jsonl"
MAX_ROUNDS = 50
RECIPES_PER_ROUND = 12
ELNORA_PROJECT_ID = "82d10329-f194-44e8-be72-e2a65bb94a7c"
ELNORA_CLI = "elnora"
MODEL = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# Elnora AI — real scientific literature agent
# ---------------------------------------------------------------------------


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


def query_elnora(question: str) -> str:
    """Send a question to Elnora AI and wait for response."""
    print(f"  [Elnora] Querying: {question[:80]}...")
    try:
        result = subprocess.run(
            [ELNORA_CLI, "tasks", "create",
             "--project", ELNORA_PROJECT_ID,
             "--title", "bio-autoresearch",
             "--message", question],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return f"(Elnora error: {result.stderr.strip()})"

        task_data = _parse_elnora_json(result.stdout)
        task_id = task_data.get("id", "")
        if not task_id:
            return "(Elnora: no task ID)"

        # Poll for response
        for elapsed in range(0, 150, 5):
            msg_result = subprocess.run(
                [ELNORA_CLI, "tasks", "messages", task_id],
                capture_output=True, text=True, timeout=30,
            )
            if msg_result.returncode == 0:
                data = _parse_elnora_json(msg_result.stdout)
                for msg in data.get("items", []):
                    if msg.get("role") == "assistant":
                        content = msg.get("content", "").strip()
                        if content:
                            print(f"  [Elnora] Got response ({len(content)} chars)")
                            return content
            time.sleep(5)

        return "(Elnora: timed out)"
    except Exception as e:
        return f"(Elnora error: {e})"


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------


def load_history() -> list[dict]:
    """Load all previous rounds from results.jsonl."""
    if not RESULTS_FILE.exists():
        return []
    rounds = []
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line.strip():
            rounds.append(json.loads(line))
    return rounds


def save_round(round_data: dict) -> None:
    """Append one round to results.jsonl."""
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(round_data) + "\n")


def format_history(history: list[dict]) -> str:
    """Format history for Claude's context."""
    if not history:
        return "No previous rounds. This is the first experiment."
    lines = []
    for r in history:
        lines.append(
            f"Round {r['round']}: best={r['best_rate']:.4f} h⁻¹ "
            f"(NaCl={r['best_recipe']['nacl_g_l']}, "
            f"Glc={r['best_recipe']['glucose_g_l']}, "
            f"YE={r['best_recipe']['yeast_extract_g_l']}) | "
            f"{r['n_recipes']} recipes | "
            f"hypothesis: {r['hypothesis'][:80]}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude API — the "researcher brain"
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an autonomous media optimization researcher for Vibrio natriegens.

Your goal: find the media composition that MAXIMIZES growth rate (h⁻¹).
Published maximum: ~4.4 h⁻¹. Current baseline: ~1.95 h⁻¹.

V. natriegens is a marine halophile — it needs salt (NaCl) for growth.
Key biology:
- Optimal NaCl: 15-25 g/L (halophile, lyses below 5 g/L)
- Glucose: carbon source, but >10 g/L can cause catabolite repression
- Yeast Extract: vitamins + amino acids, supports biomass

You think like a scientist: form hypotheses, design experiments to test them,
interpret results, and iterate. Use Elnora AI literature responses when available.

IMPORTANT: Respond ONLY with valid JSON matching the schema. No markdown, no explanation outside JSON."""

USER_TEMPLATE = """Search space:
- NaCl: {nacl_lo}-{nacl_hi} g/L
- Glucose: {glc_lo}-{glc_hi} g/L
- Yeast Extract: {ye_lo}-{ye_hi} g/L
Fixed: Tryptone 10 g/L, MOPS pH 7

{elnora_section}

Previous rounds:
{history}

Overall best so far: {overall_best}

Design {n_recipes} recipes for Round {round_num}. Return JSON:
{{
  "round": {round_num},
  "hypothesis": "your scientific reasoning for this round's strategy",
  "elnora_question": "question for literature search (null if not needed this round)",
  "recipes": [
    {{"nacl_g_l": 20.0, "glucose_g_l": 8.0, "yeast_extract_g_l": 7.0}},
    ...
  ]
}}

Rules:
- All values must be within search space bounds
- Include 1-2 "exploration" recipes outside your main hypothesis
- If results are plateauing, try something radically different
- elnora_question: set to a specific scientific question if you want literature, null otherwise"""


def call_claude(history: list[dict], elnora_context: str | None, round_num: int) -> dict:
    """Ask Claude to design the next round of experiments."""
    client = anthropic.Anthropic()

    elnora_section = ""
    if elnora_context:
        elnora_section = f"Literature from Elnora AI (real scientific search):\n{elnora_context}\n"

    overall_best = "none yet"
    if history:
        best_round = max(history, key=lambda r: r["best_rate"])
        overall_best = (
            f"{best_round['best_rate']:.4f} h⁻¹ "
            f"(Round {best_round['round']}: NaCl={best_round['best_recipe']['nacl_g_l']}, "
            f"Glc={best_round['best_recipe']['glucose_g_l']}, "
            f"YE={best_round['best_recipe']['yeast_extract_g_l']})"
        )

    bounds = SEARCH_SPACE
    user_msg = USER_TEMPLATE.format(
        nacl_lo=bounds["nacl_g_l"][0], nacl_hi=bounds["nacl_g_l"][1],
        glc_lo=bounds["glucose_g_l"][0], glc_hi=bounds["glucose_g_l"][1],
        ye_lo=bounds["yeast_extract_g_l"][0], ye_hi=bounds["yeast_extract_g_l"][1],
        elnora_section=elnora_section,
        history=format_history(history),
        overall_best=overall_best,
        n_recipes=RECIPES_PER_ROUND,
        round_num=round_num,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    return json.loads(text)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run():
    print("=" * 60)
    print("  BIO-AUTORESEARCH: Autonomous Media Optimization")
    print("  Organism: Vibrio natriegens")
    print("  Agent: Claude + Elnora AI + GP Simulator")
    print("=" * 60)
    print()

    history = load_history()
    elnora_context = None
    start_round = len(history) + 1

    if history:
        best = max(history, key=lambda r: r["best_rate"])
        print(f"Resuming from Round {start_round}. Best so far: {best['best_rate']:.4f} h⁻¹")
    else:
        # Initial Elnora query for Round 1
        print("Round 0: Querying Elnora AI for baseline literature...")
        elnora_context = query_elnora(
            "What are the optimal NaCl, glucose, and yeast extract concentrations "
            "for maximizing Vibrio natriegens growth rate? "
            "Include specific g/L values and references."
        )
        print()

    for round_num in range(start_round, start_round + MAX_ROUNDS):
        t0 = time.time()
        print(f"{'='*60}")
        print(f"  ROUND {round_num}")
        print(f"{'='*60}")

        # Step 1: Claude designs experiments
        print(f"\n[Claude] Designing round {round_num} experiments...")
        try:
            claude_response = call_claude(history, elnora_context, round_num)
        except Exception as e:
            print(f"[Claude] ERROR: {e}")
            print("Retrying in 10s...")
            time.sleep(10)
            try:
                claude_response = call_claude(history, elnora_context, round_num)
            except Exception as e2:
                print(f"[Claude] FATAL: {e2}. Skipping round.")
                continue

        hypothesis = claude_response.get("hypothesis", "no hypothesis")
        recipes = claude_response.get("recipes", [])
        elnora_question = claude_response.get("elnora_question")

        print(f"[Claude] Hypothesis: {hypothesis}")
        print(f"[Claude] Proposed {len(recipes)} recipes")

        # Step 2: Evaluate on GP simulator
        print(f"\n[Simulator] Evaluating {len(recipes)} recipes...")
        sim_result = evaluate_recipes(recipes)

        if "error" in sim_result:
            print(f"[Simulator] ERROR: {sim_result['error']}")
            # Try to fix bounds violations
            fixed_recipes = []
            for r in recipes:
                fixed = {}
                for key, (lo, hi) in SEARCH_SPACE.items():
                    fixed[key] = max(lo, min(hi, r.get(key, lo)))
                fixed_recipes.append(fixed)
            sim_result = evaluate_recipes(fixed_recipes)
            if "error" in sim_result:
                print(f"[Simulator] Still failing: {sim_result['error']}. Skipping.")
                continue
            recipes = fixed_recipes

        best_rate = sim_result["best_rate"]
        best_recipe = sim_result["best_recipe"]

        # Step 3: Log results
        round_data = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "hypothesis": hypothesis,
            "reasoning": claude_response.get("reasoning", ""),
            "elnora_question": elnora_question,
            "elnora_context": elnora_context[:500] if elnora_context else None,
            "best_rate": best_rate,
            "best_recipe": best_recipe,
            "n_recipes": len(recipes),
            "all_results": [
                {
                    "recipe": r["recipe"],
                    "mean_growth_rate": r["mean_growth_rate"],
                    "std": r["std"],
                }
                for r in sim_result["results"]
            ],
            "duration_s": round(time.time() - t0, 1),
        }
        save_round(round_data)
        history.append(round_data)

        # Step 4: Print summary
        prev_best = max((r["best_rate"] for r in history[:-1]), default=0)
        delta = best_rate - prev_best if prev_best > 0 else 0
        arrow = "▲" if delta > 0 else "▼" if delta < 0 else "="

        print(f"\n--- Round {round_num} Results ---")
        print(f"best_growth_rate: {best_rate:.4f} h⁻¹ ({arrow} {delta:+.4f})")
        print(f"best_recipe:      NaCl={best_recipe['nacl_g_l']}, Glc={best_recipe['glucose_g_l']}, YE={best_recipe['yeast_extract_g_l']}")
        print(f"duration:         {round_data['duration_s']}s")

        overall_best = max(history, key=lambda r: r["best_rate"])
        print(f"overall_best:     {overall_best['best_rate']:.4f} h⁻¹ (Round {overall_best['round']})")

        # Step 5: Query Elnora if Claude requested it
        elnora_context = None
        if elnora_question:
            print(f"\n[Elnora] Claude asked: {elnora_question[:80]}...")
            elnora_context = query_elnora(elnora_question)

        print()

    # Final summary
    print("\n" + "=" * 60)
    print("  EXPERIMENT COMPLETE")
    print("=" * 60)
    best = max(history, key=lambda r: r["best_rate"])
    print(f"Best growth rate: {best['best_rate']:.4f} h⁻¹ (Round {best['round']})")
    print(f"Best recipe: {best['best_recipe']}")
    print(f"Total rounds: {len(history)}")


if __name__ == "__main__":
    run()
