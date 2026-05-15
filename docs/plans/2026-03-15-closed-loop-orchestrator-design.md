# Closed-Loop Orchestrator Design

> **Date:** 2026-03-15 | **Status:** APPROVED | **Author:** Slava + Claude

## Problem

Automate the media optimization loop for V. natriegens: results come in from Monomer robot → agent decides what to run next → submits to robot → repeats until convergence. Currently done manually via Elnora CLI + copy-paste.

## Pattern

**Prompt Chaining with Routing** (Elnora vs BayBE based on data availability).

Not full autonomous agent — the loop is predictable, but the optimizer choice requires LLM-level reasoning.

## Architecture

```
┌──────────────────────────────────────────────────┐
│           Python Orchestrator Script              │
│         (Anthropic API + tool use)                │
│                                                   │
│  Loop:                                            │
│  1. fetch_results(plate_id)                       │
│  2. analyze_results(growth_csv)                   │
│  3. ROUTING:                                      │
│     if conditions < 8:                            │
│       → elnora_design(results_summary)            │
│     else:                                         │
│       → baybe_propose(history_df)                 │
│       → elnora_validate(proposed_conditions)      │
│  4. compile_protocol(conditions → transfer_array) │
│  5. monomer_submit(workflow)                      │
│  6. wait_for_results(poll interval)               │
│  7. check_convergence(CI overlap)                 │
│     → if converged: STOP                          │
│     → else: goto 1                                │
└──────────────────────────────────────────────────┘
        │              │              │
   ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
   │ Elnora  │   │  BayBE  │   │ Monomer │
   │  API    │   │ (local) │   │  MCP    │
   └─────────┘   └─────────┘   └─────────┘
```

## Tools (Anthropic tool_use)

### Core tools

| Tool | Input | Output | Implementation |
|------|-------|--------|----------------|
| `fetch_results` | plate_id | growth_csv DataFrame | Monomer MCP: get plate data |
| `analyze_results` | growth_csv | ranked conditions + stats | Python: parse CSV, compute growth rates, CI |
| `elnora_design` | results_summary, constraints | 10 proposed conditions (concentrations) | Elnora API: create task, send message, parse response |
| `elnora_validate` | proposed_conditions | validated conditions + warnings | Elnora API: send validation prompt |
| `baybe_propose` | history_df, n_proposals | proposed conditions (volumes) | BayBE library: `baybe_opt.py` logic |
| `compile_protocol` | conditions, plate_layout | transfer_array JSON | Python: g/L → µL conversion, volume constraints |
| `monomer_submit` | transfer_array, workflow_config | workflow_id | Monomer MCP: submit workflow |
| `check_convergence` | current_best, previous_best | {converged: bool, reason: str} | Python: CI overlap test |

### V1.5 tools (build last)

| Tool | Input | Output | Implementation |
|------|-------|--------|----------------|
| `random_screen` | n_conditions, factor_ranges | conditions (LHS/Sobol) | Python: existing code from `agent.py` |
| `ofat_design` | best_condition, factor_to_vary, range | conditions | Python: vary one factor, fix others |

## Routing Logic

```python
def select_optimizer(round_num, n_unique_conditions):
    if n_unique_conditions < 8:
        return "elnora"   # Not enough data for surrogate model
    else:
        return "baybe"    # Surrogate model is reliable
```

When BayBE is selected, Elnora still validates the proposed conditions for biological plausibility (precipitation, osmolarity, known inhibition thresholds).

## Context Strategy

Each orchestrator step receives a structured state:

```python
state = {
    "round": 2,
    "history": [
        {"condition": "HB-1", "growth_rate": 1.616,
         "params": {"YE": 7, "Tryp": 13, "Glut": 50},
         "base_media": "High Buffer Defined"},
        # ... all historical conditions
    ],
    "best": {"condition": "HB-1", "growth_rate": 1.616},
    "dropped_media": ["LBv2", "Novel Bio"],
    "constraints": {
        "wells_per_round": 8,
        "max_transfer_vol": 180,
        "min_pipette_vol": 5,
        "reagent_compatibility": {
            "never": ["CaCl2 + K2HPO4", "CaCl2 + Novel Bio"],
            "conditional": ["MgSO4 + K2HPO4 (needs 12.5mM citrate)"]
        }
    }
}
```

Elnora prompt template:
```
"V. natriegens in {base_media} gave growth rate {best_rate}/hr
with {best_params}. We have {wells} wells for round {round}.
{specific_question_based_on_context}"
```

## Convergence (Stop Condition)

Statistical: 95% CI of best condition in current round overlaps with 95% CI of best condition in previous round.

```python
def check_convergence(current_best, previous_best):
    ci_current = (current_best.mean - 1.96*current_best.se,
                  current_best.mean + 1.96*current_best.se)
    ci_previous = (previous_best.mean - 1.96*previous_best.se,
                   previous_best.mean + 1.96*previous_best.se)
    overlap = ci_current[0] <= ci_previous[1] and ci_previous[0] <= ci_current[1]
    return overlap
```

## Failure Modes

| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Elnora timeout (>120s) | Request timeout | Retry 1x, then fallback to BayBE |
| BayBE proposes invalid volumes | `is_valid_condition()` | `_enforce_volume_constraint()` + re-sample |
| Precipitation in proposed conditions | Compatibility matrix check | Auto-fix: K2HPO4→KH2PO4, remove CaCl2+phosphate |
| All wells give NaN growth rate | All mu_max = NaN | Alert + revert to baseline |
| Monomer MCP down | Connection error | Retry 2x, then stop and alert |

## File Structure

```
scripts/
├── orchestrator.py        # Main loop + Anthropic API client
├── tools/
│   ├── elnora_client.py   # Elnora API wrapper (tasks create/send)
│   ├── baybe_tools.py     # BayBE propose (from baybe_opt.py)
│   ├── monomer_client.py  # Monomer MCP wrapper
│   ├── analyzer.py        # Growth rate analysis, CI, ranking
│   ├── compiler.py        # Conditions → transfer_array
│   └── validators.py      # Precipitation check, volume constraints
├── baybe_opt.py           # Existing (reuse)
└── agent.py               # Existing (cannibalize for parts)
```

## V1 Scope (build now)

1. `orchestrator.py` — main loop with Anthropic API tool_use
2. `elnora_client.py` — wrap `elnora tasks create` + `send` + parse
3. `baybe_tools.py` — extract from `baybe_opt.py`
4. `compiler.py` — conditions → transfer_array (extract from `agent.py`)
5. `analyzer.py` — parse Monomer CSV, compute growth rates + CI
6. `validators.py` — precipitation rules from Reagent Compatibility Guide

## V1.5 (build last)

7. `random_screen` tool (LHS/Sobol — code exists in `agent.py`)
8. `ofat_design` tool

## Deferred to V2

- DOE tool (fractional factorial)
- LLM-driven strategy selection from 4+ strategies
- Full autonomy without any human checkpoint
- Eval framework
- Streamlit dashboard integration

## Simplification Check

Could this be simpler? **No.** Each component maps to a real step that was performed manually. The orchestrator just automates the exact human workflow:
1. Look at plate results → `fetch_results` + `analyze_results`
2. Ask Elnora what to do → `elnora_design` or `elnora_validate`
3. Run BayBE → `baybe_propose`
4. Calculate volumes → `compile_protocol`
5. Submit to robot → `monomer_submit`
6. Check if we're done → `check_convergence`
