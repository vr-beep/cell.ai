# Cell.ai Closed-Loop Orchestrator

Autonomous media optimization agent for V. natriegens. Closes the loop: results → Elnora/BayBE → protocol → robot → repeat.

## Quick Start

### Simulate a workflow (no API keys needed)

```bash
python scripts/simulate.py path/to/workflow.py
```

Takes a Monomer workflow `.py` file as input, returns simulated growth rates. GP surrogate trained on Round 1 real data.

```
$ python scripts/simulate.py Downloads/cellai_round3_combined.py

Reading: Downloads/cellai_round3_combined.py
Transfers: 68
Wells: ['D8', 'F10', 'F11', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9']

============================================================
RESULTS
============================================================
Well     Growth Rate (/hr)    Max OD600
-------- -------------------- ------------
F2       1.5832               0.4521
F7       1.4203               0.3892
...
```

Options:
- `--delay 10` — simulate incubation wait (seconds)
- `--json` — output raw JSON

### Run the full closed loop

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
SIMULATION_MODE=1 python scripts/orchestrator.py --plate-id PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ --auto-approve
```

The orchestrator (Claude via Anthropic API) autonomously:
1. Fetches results from Monomer (or simulator)
2. Analyzes growth rates, ranks conditions
3. Routes to BayBE (>=8 conditions) or Elnora (<8 conditions)
4. Compiles transfer_array for the robot
5. Submits workflow
6. Checks convergence (95% CI overlap) → stops or loops

Flags:
- `SIMULATION_MODE=1` — use GP simulator instead of real Monomer robot
- `--auto-approve` — skip human confirmation before robot submission
- `--resume` — resume from last saved state after crash

### Run against real Monomer robot

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python scripts/orchestrator.py --plate-id <your-plate-id>
```

Requires network access to Monomer workcell (192.168.68.60).

## Architecture

```
orchestrator.py (Claude + Anthropic API tool_use)
    │
    ├── tools/analyzer.py        — parse growth CSV, rank, compute CI
    ├── tools/baybe_tools.py     — BayBE Bayesian optimization
    ├── tools/elnora_client.py   — Elnora AI for experiment design
    ├── tools/compiler.py        — conditions → transfer_array
    ├── tools/monomer_client.py  — submit/fetch from Monomer or simulator
    ├── tools/validators.py      — convergence check
    ├── tools/growth_simulator.py — GP surrogate (replaces robot)
    └── tools/random_screen.py   — LHS sampling for initial screening

simulate.py — standalone CLI to test a workflow file against the simulator
```

## How the simulator works

GP (Gaussian Process) trained on 10 real Round 1 data points. When new conditions are submitted:

1. Parses volumes from transfer_array (same format as real Monomer)
2. GP predicts growth rate for those volumes + adds ~8% noise
3. Generates logistic OD600 curve (9 timepoints, 90 min)
4. If conditions are far from training data → returns baseline ~1.0/hr
5. After each round, GP refits on all data (real + simulated)

The simulator is a drop-in replacement for Monomer — controlled by `SIMULATION_MODE=1` env var. The orchestrator doesn't know the difference.

## Tests

```bash
SIMULATION_MODE=1 python -m pytest tests/ -v
```

38 tests covering all tools, simulator lifecycle, and full integration loop.

## Reagent Plate Layout (Team Elnora)

```
     1                  2                 3              4
  ┌──────────────────┬─────────────────┬──────────────┬──────────────────┐
A │ Novel Bio        │ LBv2            │ Def-Minimal  │ Semi-Defined     │
  │ 8320 µL          │ 8320 µL         │ 8320 µL      │ 8320 µL          │
  ├──────────────────┼─────────────────┼──────────────┼──────────────────┤
B │ High Buffer Def  │ Def-Glycerol    │ Water        │ NaCl 5M          │
  │ 9000 µL          │ 8320 µL         │ 9000 µL      │ 5000 µL          │
  ├──────────────────┼─────────────────┼──────────────┼──────────────────┤
C │ MOPS 1M          │ Glucose         │ (empty)      │ Yeast Extract    │
  │ 5000 µL          │ 5000 µL         │              │ 5000 µL          │
  ├──────────────────┼─────────────────┼──────────────┼──────────────────┤
D │ NH4SO4 1M        │ MgSO4 1M        │ Trace 1000x  │ Glycerol 10%     │
  │ 3000 µL          │ 3000 µL         │ 2000 µL      │ 3000 µL          │
  └──────────────────┴─────────────────┴──────────────┴──────────────────┘
```
