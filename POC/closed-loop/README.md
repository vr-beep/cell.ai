# Cell.ai Closed-Loop POC

Autonomous cell culture media optimization agent for V. natriegens.
Integrates **Monomer MCP** (robot control) + **Elnora AI** (literature/experiment design) + **BayBE** (Bayesian optimization) via Claude orchestrator.

Built at the 24hr AI Science Cell Culture Hack @ Monomer Bio, March 14-15, 2026.

## What This Does

```
orchestrator.py (Claude + Anthropic API tool_use)
    │
    ├── tools/analyzer.py        — parse growth CSV, rank, compute CI
    ├── tools/baybe_tools.py     — BayBE Bayesian optimization
    ├── tools/elnora_client.py   — Elnora AI for experiment design
    ├── tools/compiler.py        — conditions (g/L) → transfer_array (µL)
    ├── tools/monomer_client.py  — submit/fetch from Monomer or simulator
    ├── tools/validators.py      — convergence + precipitation checks
    ├── tools/growth_simulator.py — GP surrogate (replaces real robot)
    └── tools/random_screen.py   — LHS sampling for initial screening
```

Each round: fetch results → analyze growth → BayBE proposes → compile protocol → submit to robot → check convergence → repeat.

## Quick Start

### 1. Setup

```bash
cd POC/closed-loop
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
```

### 2. Run simulator (no API keys needed)

```bash
python scripts/simulate.py workflows/workflow_round2_20260315_032508.json
```

### 3. Run full closed loop (simulation mode)

```bash
source .env
SIMULATION_MODE=1 python scripts/orchestrator.py \
  --plate-id PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ \
  --auto-approve
```

### 4. Run against real Monomer robot

```bash
source .env
python scripts/orchestrator.py --plate-id <your-plate-id>
```

Requires network access to Monomer workcell (192.168.68.60).

### 5. Run tests

```bash
SIMULATION_MODE=1 python -m pytest tests/ -v
```

38 tests covering all tools, simulator lifecycle, and full integration loop.

### 6. Dashboard

```bash
streamlit run app.py
```

## Key Flags

- `SIMULATION_MODE=1` — GP simulator instead of real robot
- `--auto-approve` — skip human confirmation before robot submission
- `--resume` — resume from saved state after crash

## Data

- `data/` — real OD600 plate reader CSVs from Round 1-3
- `workflows/` — generated Monomer workflow JSONs
- `data/orchestrator_state.json` — persisted state for crash recovery

## Docs

- `docs/` — design docs and TDD specification
- `scripts/README.md` — detailed architecture and simulator docs
