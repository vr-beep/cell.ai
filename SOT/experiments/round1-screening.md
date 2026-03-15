# Round 1 — Actual Experiment (Submitted to Monomer MCP)

> **Date:** 2026-03-14 | **Organism:** V. natriegens | **Purpose:** Screening 3 media types
> **Status:** EXECUTED — this is the source of truth for what the robot ran.

## Plate Layout

| Well | Condition | Base (µL) | YE | Tryp | MOPS | Na L-Glut | KH₂PO₄ | Glucose | Water | Cells | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B2 | SD-1 | 129 Semi-Def | 14 | 26 | 11 | – | – | – | 0 | 20 | 200 |
| B3 | SD-2 | 128 Semi-Def | 20 | 14 | 7 | – | – | – | 11 | 20 | 200 |
| B4 | SD-3 | 125 Semi-Def | 26 | 20 | 9 | – | – | – | 0 | 20 | 200 |
| B5 | HB-1 | 110 Hi-Buf | 14 | 26 | – | 10 | – | – | 20 | 20 | 200 |
| B6 | HB-2 | 110 Hi-Buf | 20 | 14 | – | 6 | – | – | 30 | 20 | 200 |
| B7 | HB-3 | 110 Hi-Buf | 26 | 20 | – | 8 | – | – | 16 | 20 | 200 |
| B8 | LB-1 | 130 LBv2 | – | – | 12 | – | 10 | 18 | 10 | 20 | 200 |
| B9 | LB-2 | 130 LBv2 | – | – | 16 | – | 6 | 12 | 16 | 20 | 200 |
| B10 | LB-3 | 130 LBv2 | – | – | 18 | – | 8 | 8 | 16 | 20 | 200 |
| B11 | NB-CTRL | 180 Novel Bio | – | – | – | – | – | – | 0 | 20 | 200 |

## Final Concentrations (in 200 µL)

### Semi-Defined (base: 275 mM NaCl, 40 mM MOPS, 5 g/L Tryp, 2.5 g/L YE, 2 g/L Glucose, 1 mM MgSO₄)

| Cond | YE spike g/L | Tryp spike g/L | MOPS add mM |
|---|---|---|---|
| SD-1 | 7 | 13 | +55 |
| SD-2 | 10 | 7 | +35 |
| SD-3 | 13 | 10 | +45 |

### High Buffer Defined (base: 275 mM NaCl, 100 mM MOPS, 4 g/L Glucose, 1 mM MgSO₄)

| Cond | YE g/L | Tryp g/L | Na L-Glut mM |
|---|---|---|---|
| HB-1 | 7 | 13 | 50 |
| HB-2 | 10 | 7 | 30 |
| HB-3 | 13 | 10 | 40 |

### LBv2 (base: 375 mM NaCl, 10 g/L Tryp, 5 g/L YE, 4 mM KCl, 2 mM MgSO₄)

| Cond | MOPS mM | KH₂PO₄ mM | Glucose g/L |
|---|---|---|---|
| LB-1 | 60 | 50 | 9 |
| LB-2 | 80 | 30 | 6 |
| LB-3 | 90 | 40 | 4 |

### Control

| Cond | Base | Notes |
|---|---|---|
| NB-CTRL | 180 µL Novel Bio | Pure NBxCyclone, no spikes |

## Notes

- No Sodium Citrate was used (precipitation rescue was identified after this run)
- Glucose in LB-1 at 9 g/L may cause pH crash with only 60 mM MOPS
- Each condition: 3 replicates + 1 blank = 4 wells
- Wells B2-B11 used (10 conditions × 4 wells = 40 wells)
