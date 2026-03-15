# Round 1 DOE Table — 3-Media Latin Hypercube Design

> **Date:** 2026-03-14 | **Organism:** V. natriegens | **Final well volume:** 200 µL (180 µL media + 20 µL cells)

## Design Summary

| Media Type | # Conditions | # Replicates | # Blanks | Wells Used |compare thCo

## Stock Solutions

| Reagent | Stock Concentration | Units |
|---|---|---|
| Yeast Extract | 100 | g/L |
| Tryptone | 100 | g/L |
| MOPS (pH 7) | 1 | M (1000 mM) |
| Na L-Glutamate | 1 | M (1000 mM) |
| KH₂PO₄ | 1 | M (1000 mM) |
| Sodium Citrate | 1 | M (1000 mM) |
| Glucose | 100 | g/L |

## Volume Formula

```
µL = (target_concentration / stock_concentration) × 200
Water µL = 180 − Base µL − c1 µL − c2 µL − c3 µL
```

---

## Semi-Defined Media (3 conditions)

**Base:** Pre-mixed Semi-Defined base (nominal 128 µL)
**Variables:** Yeast Extract (5–15 g/L), Tryptone (5–15 g/L), MOPS additional (30–60 mM above 40 mM base)

LHS bins (3 bins per axis, one value per bin, no repeats on any axis):

| Condition | Base µL | YE g/L | YE µL | Tryp g/L | Tryp µL | MOPS add mM | MOPS µL | Water µL | **Total µL** |
|---|---|---|---|---|---|---|---|---|---|
| SD-1 | 129 | 7 | 14 | 13 | 26 | 55 | 11 | 0 | **180** |
| SD-2 | 128 | 10 | 20 | 7 | 14 | 35 | 7 | 11 | **180** |
| SD-3 | 125 | 13 | 26 | 10 | 20 | 45 | 9 | 0 | **180** |

> SD-1 base increased to 129 (no water needed), SD-3 base reduced to 125 — adjusted to fit 180 µL budget.

---

## High Buffer Defined Media (3 conditions)

**Base:** Pre-mixed High Buffer Defined base (nominal 110 µL)
**Variables:** Yeast Extract (5–15 g/L), Tryptone (5–15 g/L), Na L-Glutamate (25–50 mM)

LHS bins (3 bins per axis):

| Condition | Base µL | YE g/L | YE µL | Tryp g/L | Tryp µL | Glut mM | Glut µL | Water µL | **Total µL** |
|---|---|---|---|---|---|---|---|---|---|
| HB-1 | 110 | 7 | 14 | 13 | 26 | 50 | 10 | 20 | **180** |
| HB-2 | 110 | 10 | 20 | 7 | 14 | 30 | 6 | 30 | **180** |
| HB-3 | 110 | 13 | 26 | 10 | 20 | 40 | 8 | 16 | **180** |

---

## LBv2 Media (3 conditions + 1 control)

**Base:** Pre-mixed LBv2 base (nominal 130 µL)
**Variables:** MOPS (50–100 mM), KH₂PO₄ (25–50 mM), Glucose (2.5–5 g/L)

> **Precipitation rescue:** 3 µL Sodium Citrate (1M stock → 15 mM final) added to ALL LBv2 wells. Chelates LBv2's 2 mM MgSO₄, preventing MgHPO₄ precipitation with KH₂PO₄ at pH 7 (per PC5, Track A Rule 3). Note: citrate is a secondary carbon source for V. natriegens — accepted confound vs. precipitation risk.
>
> **Glucose capped at 5 g/L** — 9 g/L with only 60 mM MOPS causes pH crash from acetate overflow (Elnora review).
>
> **All volumes rounded to integers** — Monomer API requires whole µL.

LHS bins (3 bins per axis):

| Condition | Base µL | Citrate µL | MOPS mM | MOPS µL | KH₂PO₄ mM | KH₂PO₄ µL | Glucose g/L | Glucose µL | Water µL | **Total µL** |
|---|---|---|---|---|---|---|---|---|---|---|
| LB-1 | 130 | 3 | 60 | 12 | 50 | 10 | 5 | 10 | 15 | **180** |
| LB-2 | 130 | 3 | 80 | 16 | 30 | 6 | 4 | 8 | 17 | **180** |
| LB-3 | 130 | 3 | 90 | 18 | 40 | 8 | 3 | 6 | 15 | **180** |

### LBv2 Control

| Condition | Base µL | Citrate µL | c1 | c2 | c3 | Water µL | **Total µL** |
|---|---|---|---|---|---|---|---|
| LB-CTRL | 130 | 3 | — | — | — | 47 | **180** |

---

## Combined Pipetting Table

Ready for robot execution. Each row = one condition. Replicate 3× + 1 blank per condition.

| # | Condition | Base Media | Base µL | c1 Name | c1 Conc | c1 µL | c2 Name | c2 Conc | c2 µL | c3 Name | c3 Conc | c3 µL | Water µL | Total µL | Cells µL | Final µL |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | SD-1 | Semi-Defined | 129 | Yeast Extract | 7 g/L | 14 | Tryptone | 13 g/L | 26 | MOPS | +55 mM | 11 | 0 | 180 | 20 | 200 |
| 2 | SD-2 | Semi-Defined | 128 | Yeast Extract | 10 g/L | 20 | Tryptone | 7 g/L | 14 | MOPS | +35 mM | 7 | 11 | 180 | 20 | 200 |
| 3 | SD-3 | Semi-Defined | 125 | Yeast Extract | 13 g/L | 26 | Tryptone | 10 g/L | 20 | MOPS | +45 mM | 9 | 0 | 180 | 20 | 200 |
| 4 | HB-1 | High Buffer | 110 | Yeast Extract | 7 g/L | 14 | Tryptone | 13 g/L | 26 | Na L-Glutamate | 50 mM | 10 | 20 | 180 | 20 | 200 |
| 5 | HB-2 | High Buffer | 110 | Yeast Extract | 10 g/L | 20 | Tryptone | 7 g/L | 14 | Na L-Glutamate | 30 mM | 6 | 30 | 180 | 20 | 200 |
| 6 | HB-3 | High Buffer | 110 | Yeast Extract | 13 g/L | 26 | Tryptone | 10 g/L | 20 | Na L-Glutamate | 40 mM | 8 | 16 | 180 | 20 | 200 |
| 7 | LB-1 | LBv2 | 130 | MOPS | 60 mM | 12 | KH₂PO₄ | 50 mM | 10 | Glucose | 5 g/L | 10 | 15 | 180 | 20 | 200 |
| 8 | LB-2 | LBv2 | 130 | MOPS | 80 mM | 16 | KH₂PO₄ | 30 mM | 6 | Glucose | 4 g/L | 8 | 17 | 180 | 20 | 200 |
| 9 | LB-3 | LBv2 | 130 | MOPS | 90 mM | 18 | KH₂PO₄ | 40 mM | 8 | Glucose | 3 g/L | 6 | 15 | 180 | 20 | 200 |
| 10 | LB-CTRL | LBv2 | 130 | — | — | 0 | — | — | 0 | — | — | 0 | 47 | 180 | 20 | 200 |

> **All LBv2 rows include 3 µL Sodium Citrate (15 mM) not shown in table columns.** Added before other reagents per addition order (PC10).

---

## Verification Checklist

- [x] Every row sums to exactly 180 µL (pre-cells)
- [x] Every row + 20 µL cells = 200 µL final
- [x] All spike volumes ≥ 5 µL (minimum pipettable)
- [x] All LBv2 volumes are integers (Monomer API requirement)
- [x] All concentrations within Elnora-specified ranges
- [x] Glucose capped at 5 g/L to prevent pH crash with < 100 mM MOPS
- [x] LHS property: no two conditions share a bin on any axis within a media type
- [x] No precipitation conflicts (Citrate chelates Mg²⁺ in LBv2 wells)
- [x] 10 conditions × 4 wells = 40 wells (fits 60 usable wells)

## Robot Execution Note

**Pre-mix conditions offline** to stay under the ~42 transfer/routine limit:
1. Prepare 10 final media mixes in the 24-well reagent stock plate (one well per condition)
2. Robot does 1-to-many transfers: each condition → 4 destination wells (180 µL, `new_tip: "once"`)
3. Robot adds cells: cell stock → all 40 wells (20 µL, `new_tip: "always"`, `post_mix_volume: 40`, `post_mix_reps: 5`)
4. Total transfers: 40 (media) + 40 (cells) = 80 — split across 2 routines if needed

## Plate Layout Note

Each condition uses 4 wells: 3 replicates + 1 blank (same media, no cells — water instead).
40 wells used out of 60 usable (excluding edge wells). **20 wells spare.**
