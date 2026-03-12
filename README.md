# Cell.ai — Autonomous Cell Culture Media Optimization Agent

An AI agent that designs, runs, and learns from cell culture experiments autonomously on a robotic workcell.

**Event:** 24hr AI Science Cell Culture Hack @ Monomer Bio — Track A (March 14-15, 2026)

## What it does

A scientist says: "I have *V. natriegens* and these reagents — find the best growth media." The agent:

1. Reads scientific literature for constraints (via Elnora MCP)
2. Designs 14 media compositions using Bayesian optimization (BayBE)
3. Compiles g/L concentrations to µL volumes for 1 mL media stocks
4. Sends recipes to the robot (Monomer MCP) — mix, plate, incubate, read
5. Parses OD600 plate reader data → growth rates (with blank subtraction)
6. Diagnoses data quality, generates hypothesis
7. Feeds results back to BayBE → next round of compositions

The loop runs autonomously for 2-3 rounds in 10 hours of robot time.

## Architecture

```
                     ┌─────────────┐
                     │  LLM Agent  │
                     │   (brain)   │
                     └──────┬──────┘
                            │
      ┌─────────────────────┼───────────┬──────────┐
      ▼                     ▼           ▼          ▼
┌──────────┐          ┌────────┐ ┌────────┐ ┌────────┐
│  BayBE   │          │Compiler│ │Monomer │ │ Parser │
│(optimizer)│          │(g/L→µL)│ │  MCP   │ │(OD→µ)  │
└──────────┘          └────────┘ └────────┘ └────────┘

              ┌────────┐
              │ Elnora │ ← Enhancement (literature context)
              │  MCP   │
              └────────┘
```

## Optimization target

| Component | Range | Stock |
|---|---|---|
| NaCl | 10-35 g/L | 5M (292.2 mg/mL) |
| Glucose | 1-20 g/L | 100 mg/mL |
| Yeast Extract | 2-10 g/L | 100 mg/mL |
| Tryptone (fixed) | 10 g/L | 100 mg/mL |
| MOPS pH 7 (fill-up) | remainder | 1M |

**Benchmark:** Initial recipe (10 g/L Tryptone, 5 g/L YE, 10 g/L NaCl, 0 g/L Glucose in MOPS pH 7). Expected baseline growth rate: ~2.0-2.5 h⁻¹. Published ceiling: ~4.4 h⁻¹ (Hoffart 2017).

## Key docs

| Doc | What |
|---|---|
| [PRD](doc/artifacts/PRD-media-optimization-agent.md) | Full product requirements — architecture, timeline, success criteria, eval framework |
| [Experiment](doc/Experiment%20.md) | Scientist-confirmed parameters (Mar 11 sync) |
| [Knowledge Base](doc/knowledge-base/README.md) | V. natriegens biology, BayBE config, competitive landscape, hackathon playbook |
| [Hackathon Details](doc/hackathon_details.md) | Event schedule, tracks, sponsors |

## Team

| Who | What |
|---|---|
| **Slava** | Agent architecture, system integration, LLM + BayBE, dashboard, pitch |
| **Nikki** | Biological domain expertise, experiment design, live demo reaction |
| **Arne** | OD → growth rate parser, data pipeline, MCP client |

## Status

**Reviewed — Mar 12, 2026.** PRD complete. Pre-hack evals (E1 interface contracts, E3 MCP mock) scheduled for Mar 12-13. Hackathon starts Mar 14.
