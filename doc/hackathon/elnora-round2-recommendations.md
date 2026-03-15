# Elnora Round 2: Exploit Recommendations

**Task ID:** `56edeb44-b79f-4f4c-98bf-a8d2fe6e74c2`
**Date:** 2026-03-15
**Project:** Cell.ai - V.natriegens Media Optimization

## Question

Round 1 results sent with exploit strategy request — 10 conditions on HB + SD bases, optimizing growth rate only. See `docs/plans/2026-03-15-round2-exploit-workflow.md` for full prompt.

## Elnora Response

**High Buffer Defined** is the superior base for pure growth rate. **Tryptone and Na L-Glutamate are the primary drivers**.

In V. natriegens, Glutamate feeds directly into the TCA cycle (via alpha-ketoglutarate) providing massive energy and nitrogen without triggering severe acetate overflow (pH crash) caused by excess glucose. Combined with high Tryptone (pre-formed amino acids) and the 100mM MOPS already in the HB base, this is a perfect engine for rapid biomass accumulation.

For Semi-Defined, higher Yeast Extract (SD-3) outperformed higher Tryptone (SD-1).

6 wells allocated to HB (winner), 4 wells to SD (runner-up).

### Round 2: Exploit Matrix (Total Final Concentrations)

| Condition | Base Media | Component 1 (YE) | Component 2 (Tryptone) | Component 3 (Glutamate / MOPS) |
|:---|:---|:---|:---|:---|
| **HB-R2-1** | High Buffer Defined | YE 7.0 g/L | Tryp 15.0 g/L | Na L-Glut 60 mM |
| **HB-R2-2** | High Buffer Defined | YE 7.0 g/L | Tryp 17.0 g/L | Na L-Glut 50 mM |
| **HB-R2-3** | High Buffer Defined | YE 7.0 g/L | Tryp 13.0 g/L | Na L-Glut 70 mM |
| **HB-R2-4** | High Buffer Defined | YE 5.0 g/L | Tryp 15.0 g/L | Na L-Glut 60 mM |
| **HB-R2-5** | High Buffer Defined | YE 9.0 g/L | Tryp 15.0 g/L | Na L-Glut 60 mM |
| **HB-R2-6** | High Buffer Defined | YE 5.0 g/L | Tryp 17.0 g/L | Na L-Glut 70 mM |
| **SD-R2-1** | Semi-Defined | YE 17.5 g/L | Tryp 15.0 g/L | MOPS 85 mM |
| **SD-R2-2** | Semi-Defined | YE 15.5 g/L | Tryp 17.0 g/L | MOPS 85 mM |
| **SD-R2-3** | Semi-Defined | YE 17.5 g/L | Tryp 17.0 g/L | MOPS 95 mM |
| **SD-R2-4** | Semi-Defined | YE 15.5 g/L | Tryp 15.0 g/L | MOPS 95 mM |

### Strategy Breakdown

- **HB-R2-1 to 3 (The Push):** Anchor YE at winning 7 g/L, push Tryptone to 15-17 g/L and Glutamate to 60-70 mM.
- **HB-R2-4 & 5 (The YE Check):** Test if YE 5 g/L improves rate (less metabolic clutter) or 9 g/L helps support higher loads.
- **HB-R2-6 (The Max Engine):** Max Tryptone (17 g/L) + max Glutamate (70 mM) + min YE (5 g/L).
- **SD-R2-1 to 4 (The Organics Ceiling):** Push total organics to ~32-34 g/L with MOPS at 85-95 mM to handle acetate.
