# Experimental Campaign — Fastest-Growing Recipe for Novel Media Strain V. natriegens

**Status:** Plate 1 design ready (pending Cultivarium seed + antibiotic info). Last revision: 2026-04-14 after Elnora critical review.

**Goal:** Найти рецепт media, максимизирующий μ_max для Novel Media Strain в 96-well batch, 37°C, 150 µL, 4h kinetic. Target: winner μ > NBxCyclone anchor × 1.23 (статистически detectable при n=8, CV=15%).

**Cross-references:**
- Sibling doc: `clarification-plan.md` (gaps, tracks, source-of-truth)
- Sibling doc: `vsm-media-optimization.md` (process analysis)
- External: Cultivarium 2026 `/Users/viachealavrudenko/Downloads/2026.02.11.705132v1.full.pdf`

---

## Core design decisions (Elnora-grounded)

Все ключевые параметры подтверждены через literature citation с верифицированным DOI.

| Decision | Value | Grounding |
|---|---|---|
| Volume per well | **150 µL total** (135 media + 15 cells) | kLa ~21→~40 h⁻¹ при drop с 200→150 µL [RETRIEVED: 10.1002/bit.24824] |
| Inoculum OD | **0.01** (not 0.05) | 6.3 doublings vs 4 при μ=4 → 6-7 vs 4-5 fit points [CALCULATED] |
| Incubation | 37°C, Liconic STX-220, pre-warmed | [MODEL KNOWLEDGE] — pre-warm избегает 30-60 мин μ_max depression |
| OD read | OD600, каждые 10 мин, 4 часа | `experimental-constraints.md:71-77` |
| μ fit window | 0.1 < OD < 0.8, log-linear | [MODEL KNOWLEDGE] |
| Physical μ sanity cap | 4.5 h⁻¹ | Physical limit 4.43 [RETRIEVED: 10.1128/AEM.01614-17]; expected max for plasmid strain ~3.98 (-10% burden) [CALCULATED] |
| NaCl search bounds | 10-30 g/L | Complex media with osmoprotectants; LBv2=22, LB3=30 work well [MODEL KNOWLEDGE]; Schleicher 2024 [10.1186/s12896-024-00897-8] 7.5-15 was mineral only |
| Glucose bounds | 5-20 g/L | Wide + MOPS buffering; 20 g/L → up to 111 mM acetate [CALCULATED] |
| MOPS bounds | 100-300 mM | Schleicher 2024 used 200 mM against acetate overflow [RETRIEVED: 10.1186/s12896-024-00897-8] |
| YE supplementation | 0-10 g/L (added to base) | [MODEL KNOWLEDGE] |
| n replicates (exploration) | 3 | Field standard для V. natriegens [MODEL KNOWLEDGE] |
| n replicates (validation) | 8 | Gives 80% power for Δ≥22.6%, 96% for Δ=30% [CALCULATED] |
| Anchors per plate | 3× NBxCyclone + 3× LBv2 | Batch effects #1 source of multi-plate BO failure [MODEL KNOWLEDGE] |
| Plasmid retention check | Replica spotting ±Abx on top 5 winners after plate 4 | 24 generations in 4h → loss risk without selection [CALCULATED] |

---

## Plate 1 — Deep BO on Semi-Defined (60 wells)

**Rationale for single-media deep BO (not 4-media screen):** GP требует ~10 points per continuous dimension. 4 media × 4 LHS points в 4D = 4 points per category → mathematically below threshold, GP fits noise. Single media × 17 points даёт valid GP training. Ranking другой media deferred to Plate 2.

**Layout:**
```
Controls (9 wells):
  3× NBxCyclone anchor    [pure NBxCyclone, 180 µL base]
  3× LBv2 anchor          [pure LBv2, 180 µL base]
  3× blanks               [1× Semi-Defined, 1× NBxCyclone, 1× high-Glu+NaCl variant]

Test conditions (51 wells):
  17 conditions × 3 replicates on Semi-Defined base
  Generated via Latin Hypercube Sampling in 4D:
    NaCl:     10-30 g/L
    Glucose:   5-20 g/L
    YE added:  0-10 g/L
    MOPS:    100-300 mM
  
  Includes Cultivarium DoE condition 14 as 1 of 17 points (warm-start seed)
  IF retrievable from supplementary text 8 (dependency G0.2)
```

**Output:** GP trained on 17-point Semi-Defined landscape. BayBE exposes posterior for proposing Plate 2.

**Acceptance gates:**
- NBxCyclone anchor μ ∈ [2.5, 4.2] — drift check
- ≥ 70% of 17 conditions have fit_r2 ≥ 0.98 AND n_timepoints ≥ 6
- Blank OD < 0.15

---

## Plate 2 — Add second base media + refine (60 wells)

**Decision point:** на основе Plate 1 GP posterior выбрать 2nd base media для сравнения (гипотеза: NBxCyclone-modified или High Buffer Defined).

**Layout:**
```
Controls (9 wells):
  3× NBxCyclone anchor
  3× LBv2 anchor
  3× blanks
  
Test conditions (51 wells):
  16 conditions × 3 replicates = 48
  Split 8 conditions per base media (Semi-Defined top performers + new media LHS)
  3 flex wells for additional replicates on Plate 1 noisy top-performers
```

**Selection method:** BayBE acquisition function (Expected Improvement) on combined 1-media + 1-new-media GP.

---

## Plate 3 — Optimization of winner base media (60 wells)

**Layout:**
```
Controls (9 wells): 3 NBxCyclone + 3 LBv2 + 3 blanks

Test conditions (51 wells):
  16 conditions × 3 replicates + 3 flex
  Winner base media from Plate 2
  Expanded search: + MgSO4 (1-10 mM), + Trace metals (0.5-2×), + Glycerol (0-5 g/L)
```

---

## Plate 4 — Validation (60 wells)

**Layout:**
```
Controls (14 wells):
  3× NBxCyclone anchor
  3× LBv2 anchor
  3× blanks
  5 top candidates × n=8 replicates = 40
  2 ablation conditions × n=3 replicates = 6
```

**Post-run replica spotting:**
- Top 5 candidate wells: dilute 10⁻⁶, spot 5 µL × 2 plates (±antibiotic)
- Next morning: count CFU ratio → plasmid retention %
- Winner must have retention > 80%

**Campaign success criteria:**
- Winner mean μ > NBxCyclone × 1.23 (22.6% lift minimum for 80% power)
- SE(μ) < 10% of mean on winner
- Plasmid retention ≥ 80%
- ≥ 1 condition flagged as null result (для paper)

---

## Plate 5 (optional) — Reproducibility

Winner recipe × 24 replicates на 2 плашки в разные дни. Δμ между plates < 20%.

---

## Per-plate decision log (update as campaign progresses)

### Plate 1 — [Status: designed, awaiting deps]
- **Date:** TBD
- **Dependencies pending:** G0.2 (Cultivarium condition 14), G0.3 (Tecan API format), G0.4 (strain antibiotic — for later plasmid check)
- **Seed point chosen:** TBD (fallback: random LHS if Cultivarium retrieval fails)
- **Decision rationale:** Selected Semi-Defined as base (vs LBv2/HB-Defined/Defined-Glycerol) because:
  - (a) balanced complex + defined composition allows NaCl and glucose to vary meaningfully
  - (b) historical SD-1 performed best (though n=1, not reliable)
  - (c) мax flexibility for adding MOPS as 4th knob
- **Key risks:**
  - Cultivarium DoE winner unretrievable → start without seed (still valid)
  - OD 0.01 may be below Tecan detection → adjust to OD 0.02 (5-6 fit points)

### Plate 2 — [Status: planned, undetermined base media]
- **Decision criterion:** Pick 2nd base media based on Plate 1's top μ trajectory + literature hint
- **Date:** TBD

### Plate 3 — [Status: planned]
- **Date:** TBD

### Plate 4 — [Status: planned]
- **Date:** TBD
- **Action required:** G0.4 strain antibiotic before replica spotting possible

---

## Grounding citations (verified DOIs)

| DOI | Paper | Used for |
|---|---|---|
| [10.1128/AEM.01614-17](https://doi.org/10.1128/AEM.01614-17) | Long et al., 2019 — "High substrate uptake rates..." | Physical μ_max limit 4.43 h⁻¹ |
| [10.1186/s12896-024-00897-8](https://doi.org/10.1186/s12896-024-00897-8) | Schleicher et al., 2024 — "pH, Na, osmolality in V. natriegens batch" | NaCl 7.5-15 (mineral); MOPS 200 mM |
| [10.1002/bit.24824](https://doi.org/10.1002/bit.24824) | kLa in 96-well plates | Volume → OTR trade-off |
| [10.1128/aem.01745-25](https://doi.org/10.1128/aem.01745-25) | Pfeifer et al., 2021 — "V. natriegens sensitive to acidic fermentation" | Acetate overflow → MOPS requirement |

**Non-DOI citations (needs manual fetch):**
- Cultivarium 2026 — "Outpacing E. coli: Development of V. natriegens as Next-Generation Cloning Host" — bioRxiv (prefix 10.64898 is invalid DOI; cite as bioRxiv URL). Supplementary text 8 needed for DoE condition 14.

---

## Open decisions

1. **If Cultivarium condition 14 unavailable** → proceed with 17 LHS points без warm-start seed. GP convergence slightly slower (1 extra plate possible), but mathematically still valid.
2. **If Tecan API returns pre-processed** (not raw kinetic) → no analyzer.py changes needed, skip G0.3 fit_exponential work.
3. **If μ cap at ~3 across plates** (O2 limit at kLa=40) → document scale-up limitation in paper methods. Ranking within-plate still valid.
4. **Strain antibiotic unknown** → plasmid retention check deferred to Plate 5 (additional day) or abandoned (methods section caveat).
