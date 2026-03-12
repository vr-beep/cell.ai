# Cell.ai Knowledge Base

> Reference materials for building an autonomous AI agent that optimizes cell culture media on a robotic workcell. Compiled March 11, 2026.

---

## Contents

| # | File | What's In It |
|---|------|-------------|
| 01 | [Competitive Landscape](01-competitive-landscape.md) | TetraScience, Synthace, Culture Bio, Strateos, Opentrons (pipette specs!), Monomer Bio, BioMARS, ISLFCC, Emerald Cloud Lab. Positioning matrix. |
| 02 | [BayBE Deep Dive](02-baybe-deep-dive.md) | Key papers (Nature Comms, Digital Discovery, Biotech & Bioeng), BayBE architecture, parameter types, constraints, recommenders, acquisition functions, serialization. Practical config for hackathon. |
| 03 | [Closed-Loop Architectures](03-closed-loop-architectures.md) | ChemOS 2.0, Atlas, LIRA. Core loop pattern. Failure modes (MCP, plate reader, volume accuracy). Opentrons Flex accuracy table. g/L→µL conversion math + pitfalls. 96-well plate layout. Error handling patterns. Elnora AI + Augmented Nature. |
| 04 | [Hackathon Playbook](04-hackathon-playbook.md) | Previous Monomer Bio hack insights. iGEM V. natriegens precedent. Judge criteria. Common mistakes. "One slide, four numbers" format. Demo pitch structure. Head-to-head differentiation. Streamlit dashboard patterns. Pre-demo checklist. |
| 05 | [V. natriegens Biology](05-v-natriegens-biology.md) | Published media compositions (LBv2, BHIN, defined). Growth rate data table. NaCl sensitivity (15-25 g/L optimal). Glucose utilization + acetate warning. Yeast extract (uncharacterized — novel!). MOPS buffer importance. OD600 measurement artifacts. Edge effects. Blank subtraction protocol. No prior BO/DOE study exists (our work is novel). |

---

## Quick Reference: Critical Numbers

| Parameter | Value | Source |
|-----------|-------|--------|
| V. natriegens max growth rate | 4.43 h-1 (9.4 min doubling) in BHIN | Hoffart 2017 |
| NaCl optimum | 15-25 g/L (1.5-2.5%) | Long et al. 2019 |
| NaCl upper tolerance | ~30 g/L before inhibition | Literature consensus |
| Glucose uptake rate | 3.90 g/g/h (2x E. coli) | Long et al. 2017 |
| Opentrons Flex min reliable volume | 10 µL (5 µL minimum, ±8-10% error) | Opentrons docs |
| Plate edge effect (outer wells) | 16-35% reduction in activity | Mansoury et al. 2021 |
| Usable wells per 96-well plate | 60 (inner grid only) | Standard practice |
| Conditions per plate (our layout) | 14 + 1 control (4 wells each) | Scientist sync Mar 11 |
| Incubation time | 2-4 hours at 37C | Scientist sync Mar 11 |
| Max rounds before midnight | 2-3 | Timeline calculation |
| BayBE convergence (3 components) | Expected 2-4 rounds | Literature extrapolation |

---

## Key Warnings

1. **Glucose + NaCl create OD600 particles** — always use blank wells for subtraction
2. **Glucose drops pH via acetate production** — MOPS buffer is essential when glucose > 5 g/L
3. **Never dispense < 5 µL on Opentrons Flex** — accuracy drops to ±8-10%
4. **Do NOT store V. natriegens at 4C** — enters viable-but-nonculturable state
5. **No prior BO study on V. natriegens media exists** — our work is genuinely novel
6. **Plate reader OD ≠ spectrophotometer OD** — shorter path length, ~2.5x conversion factor
