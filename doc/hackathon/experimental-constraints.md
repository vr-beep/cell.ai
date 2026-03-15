# Experimental Setup Limitations

Hard constraints the optimization agent must respect. These cannot be changed during the hackathon.

## Robot Constraints

| # | Limitation | Value |
|---|-----------|-------|
| R1 | Liquid handler | Opentrons Flex |
| R2 | Max liquid transfers per routine | 40–60 (tip/deck limitation) |
| R3 | Final volume per well | 200 µL (180 µL reagent + 20 µL cell inoculum) |
| R4 | Minimum pipettable volume | ~10 µL (accuracy degrades below ~5 µL) |
| R5 | Tip reuse | `new_tip: "once"` reuses tip; `new_tip: "always"` uses fresh tip per transfer |
| R6 | Blow out | `blow_out: False` for cell transfers (avoids bubbles before absorbance reading) |
| R7 | Post-mix for cell inoculation | 5 reps at 40 µL recommended |
| R8 | First workflow requires Monomer staff approval | Subsequent workflows auto-approved |

### Transfer Array Format

The robot accepts a JSON array of transfer objects:

```json
{
  "src_plate": "reagent" | "cell_culture_stock",
  "src_well": "A1",
  "dst_plate": "experiment",
  "dst_well": "A1",
  "volume": 180,
  "new_tip": "once" | "always",
  "blow_out": true | false,
  "post_mix_volume": 40,
  "post_mix_reps": 5
}
```

## Labware Constraints

| # | Limitation | Value |
|---|-----------|-------|
| L1 | Experiment plate | 96-well flat-bottom (Scienfocus), **220 µL max per well** |
| L2 | Reagent stock plate | 24-well deep well V-bottom (CellPro), 8.5 mL max per well |
| L3 | Cell culture stock plate | 24-well flat-bottom (Lichen Cottage), 2.2 mL max per well, ~2 mL cell culture |
| L4 | Plates on deck per routine | 3 (reagent stock + experiment + cell culture stock) |

## Plate Layout Constraints

| # | Limitation | Value |
|---|-----------|-------|
| P1 | Plate format | 96-well flat-bottom, 220 µL max |
| P2 | Usable wells | 60 (outer wells excluded — edge effects) |
| P3 | Wells per condition | 4 (3 replicates + 1 media-only blank) |
| P4 | Max conditions per plate | 10 test + 1 positive control = 11 total |
| P5 | Plate reuse | None — fresh plate per round |
| P6 | Blank wells required | Yes — Glucose + NaCl create OD600 particle artifacts |

## Time Constraints

| # | Limitation | Value |
|---|-----------|-------|
| T1 | Hackathon duration | 24 hours |
| T2 | Incubation per round | 2–4 hours (V. natriegens lag phase is 15–90+ min after media switch) |
| T3 | Max optimization rounds | 2–3 (includes robot prep, reading, BayBE analysis) |
| T4 | Total experiments possible | 20–30 (10 conditions × 2–3 rounds) |
| T5 | Kinetic reads available | Measure absorbance every 10 min for up to 2 hours per workflow |

## Measurement Constraints

| # | Limitation | Value |
|---|-----------|-------|
| M1 | Reader | Tecan Infinite plate reader |
| M2 | Measurement | OD600 (optical density at 600 nm) |
| M3 | Path length at 200 µL | ~0.56 cm (reads ~2× lower than 1 cm cuvette) |
| M4 | OD600 linear range | 0.1–0.8 (above 0.8 must dilute) |
| M5 | Noise floor | < 0.05 corrected OD is unreliable |
| M6 | Blank subtraction | Required before any calculation |
| M7 | Doubling time < 10 min | Artifact — not real growth |
| M8 | Kinetic mode | Every 10 min for up to 2 hours — gives full growth curve, not just endpoint |

## Stock Solution Constraints

| # | Limitation | Value |
|---|-----------|-------|
| S1 | Available stocks (core) | Tryptone 100 mg/mL, YE 100 mg/mL, NaCl 5M, Glucose 100 mg/mL, MOPS 1M pH 7 |
| S2 | Available stocks (divalent cations) | MgSO₄ 1M, CaCl₂ 1M, FeSO₄ 1M |
| S3 | Available stocks (phosphate) | K₂HPO₄ 1M (pH ~8.7), KH₂PO₄ 1M (pH ~4.5) |
| S4 | Available stocks (nitrogen/other) | (NH₄)₂SO₄ 1M, KCl 2M, Sodium L-Glutamate 1M |
| S5 | Available stocks (carbon) | Glycerol 10% in sterile H₂O |
| S6 | Available stocks (chelator) | Sodium Citrate 1M |
| S7 | Available stocks (pH adjust) | HCl 12N, NaOH 10N |
| S8 | Available stocks (trace) | Trace metals 1000× |
| S9 | Pre-made media available | See Pre-Made Media Reference below |
| S10 | Reagent stock plate capacity | 24 wells × 8.5 mL max per well |
| S11 | Stock concentrations are fixed | Cannot prepare new dilutions during hack |
| S12 | Monomer can prepare up to 2 composed media | e.g., LBv2 or Minimal Defined, plus dilutions of existing stocks |
| S13 | Stock plate modifiable between iterations | Solutions can be added/replaced if precipitation occurs |
| S14 | Max volume from any single stock | Limited by 200 µL final volume minus other components |

## Search Space Constraints (Defined by Elnora AI — 2026-03-14)

### Component Selection (Elnora Q1)

Elnora ranked all 13 components by expected impact on V. natriegens growth rate:

| Rank | Component | Recommendation | Rationale |
|------|-----------|---------------|-----------|
| 1 | Yeast Extract | **OPTIMIZE** | Provides pre-formed amino acids, vitamins, nucleotides — V. natriegens scavenges rather than synthesizes de novo. NBxCyclone uses 15 g/L. |
| 2 | Tryptone | **OPTIMIZE** | Complex nitrogen source. Ratio of YE:Tryptone dictates max carrying capacity. |
| 3 | MOPS (Buffer) | **OPTIMIZE** | V. natriegens rapidly acidifies media via acetate overflow metabolism. If pH drops below ~6.0, growth halts. Buffer capacity is the secret weapon. |
| 4 | Glucose | Fix at 0.2% or 0% | With high YE/Tryptone, cells have plenty of carbon. High glucose risks pH crash via acetate. |
| 5 | NaCl | Fix at 275 mM | Halophilic requirement met; broad tolerance range (0.5–2.0%). No need to waste DOE space. |
| 6 | KH₂PO₄ | Fix at 10 mM | Essential P source. Use monobasic only. |
| 7 | MgSO₄ | Fix at 2 mM | Essential for ribosome stability. 2 mM is sufficient. |
| 8 | Sodium L-Glutamate | Exclude | Redundant with rich complex media (YE/Tryptone). |
| 9 | (NH₄)₂SO₄ | Exclude | Redundant with complex nitrogen; adds unnecessary osmotic stress. |
| 10 | KCl | Exclude | Not needed with NaCl providing adequate ionic strength. |
| 11 | K₂HPO₄ | **Exclude** | Precipitation risk with divalent cations. Use KH₂PO₄ instead. |
| 12 | CaCl₂ | **Exclude** | Immediate precipitation with phosphates, sulfates, and citrate. |
| 13 | FeSO₄ | **Exclude** | Precipitates with phosphate; oxidizes to Fe(OH)₃ at pH 7. |

**Top 3 optimization parameters: Yeast Extract, Tryptone, MOPS**

### Concentration Ranges (Elnora Q2)

Formula: `Volume (µL) = (Target / Stock_Concentration) × 200`

**Parameter 1: Yeast Extract (Stock: 100 mg/mL = 100 g/L)**

| Level | Concentration | Volume (µL) |
|-------|--------------|-------------|
| 1 | 2.5 g/L | 5 |
| 2 | 5.0 g/L | 10 |
| 3 | 10.0 g/L | 20 |
| 4 | 15.0 g/L | 30 |
| 5 | 20.0 g/L | 40 |
| 6 | 25.0 g/L | 50 |

**Parameter 2: Tryptone (Stock: 100 mg/mL = 100 g/L)**

| Level | Concentration | Volume (µL) |
|-------|--------------|-------------|
| 1 | 2.5 g/L | 5 |
| 2 | 5.0 g/L | 10 |
| 3 | 10.0 g/L | 20 |
| 4 | 15.0 g/L | 30 |

**Parameter 3: MOPS pH 7 (Stock: 1M)**

| Level | Concentration | Volume (µL) |
|-------|--------------|-------------|
| 1 | 25 mM | 5 |
| 2 | 50 mM | 10 |
| 3 | 75 mM | 15 |
| 4 | 100 mM | 20 |
| 5 | 125 mM | 25 |
| 6 | 150 mM | 30 |

### Volume Budget Verification

| Component | Min µL | Max µL | Notes |
|-----------|--------|--------|-------|
| YE (optimize) | 5 | 50 | |
| Tryptone (optimize) | 5 | 30 | |
| MOPS (optimize) | 5 | 30 | |
| NaCl 275 mM (fixed) | 11 | 11 | 275/5000 × 200 |
| KH₂PO₄ 10 mM (fixed) | 2 | 2 | Below min pipettable — combine with water or fix at 5 mM (1 µL) |
| MgSO₄ 2 mM (fixed) | 0.4 | 0.4 | Below min pipettable — use trace metals only or pre-dilute |
| Trace metals 1× (fixed) | 0.2 | 0.2 | Below min — pre-dilute to 100× for 2 µL |
| **Total reagents** | **~28** | **~124** | |
| **Water to 180 µL** | **56** | **152** | |

**Max combination (50+30+30+11+2+0.4+0.2 = ~124 µL) leaves 56 µL for water. VERIFIED: fits in 180 µL.**

> **⚠️ Pipetting concern:** KH₂PO₄ (2 µL), MgSO₄ (0.4 µL), and Trace metals (0.2 µL) are below the 5 µL accuracy threshold. Options: (a) pre-dilute stocks, (b) prepare a "mineral premix" combining these three, or (c) Monomer prepares a diluted working stock.

### Toxicity Flags (Elnora Q2)

| Flag | Risk | Mitigation |
|------|------|------------|
| Glucose-induced pH crash | High glucose (>10 g/L) → rapid acetate production → pH < 5.5 | High MOPS (100+ mM) required if including glucose |
| Osmotic stress | NaCl > 500 mM + high solutes → extended lag | Keep NaCl ≤ 375 mM |
| Ammonia toxicity | High YE (20-25 g/L) → amino acid catabolism releases NH₃ | Monitor pH; ensure carbon source doesn't deplete first |

### Experimental Strategy (Elnora Q3)

**Recommended: Hybrid LHS → BayBE (Strategy G)**

| Round | Strategy | Purpose | Conditions |
|-------|----------|---------|------------|
| 1 | Latin Hypercube Sampling (LHS) or D-optimal | Exploration — map global landscape | 10 |
| 2 | BayBE (balanced qEI/qUCB) | Exploitation + exploration | 10 |
| 3 | BayBE (exploitation-heavy, low β) | Maximize growth rate | 10 |

**Key strategy decisions:**

1. **Round 1 ≠ Rounds 2-3.** LHS for space-filling initialization; BayBE for sequential optimization.
2. **Batch size: 10** per round (matches plate layout).
3. **10-10-10 split** across 3 rounds.
4. **Classical DOE is NOT appropriate** — budget too small (30/343 = 8.7% of space). Use algorithmic DOE (D-optimal or LHS) for Round 1 only.
5. **Use µ_max (not endpoint OD)** as the target metric. Extract from kinetic reads: max slope of ln(OD) vs. time during exponential phase.
6. **No cross-round replicates needed** — LBv2 positive control on every plate serves as normalizer. Feed BayBE the **relative growth rate** (µ_max,condition / µ_max,LBv2) to control batch effects.

**BayBE Configuration:**

| Setting | Value | Rationale |
|---------|-------|-----------|
| Parameter encoding | Continuous/numerical | Allows GP to interpolate between discrete levels |
| Surrogate model | Gaussian Process (GP) | Gold standard for <50 data points; excellent uncertainty quantification |
| Acquisition function | q-Expected Improvement (qEI) or q-Upper Confidence Bound (qUCB) | Batch-aware; prevents suggesting 10 near-identical points |
| Round 3 tweak | Lower β (exploration weight) in qUCB | Force exploitation of best known regions |

## Volume Compiler (All 13 Stocks)

Stock solutions must be converted from targets → µL pipetting volumes for **200 µL final volume** (180 µL reagent + 20 µL cells).

| # | Stock | Concentration | Conversion formula | Status |
|---|-------|--------------|-------------------|--------|
| 1 | Tryptone | 100 mg/mL (100 g/L) | target_g_per_L / 100 × 200 µL | **OPTIMIZE** (2.5–15 g/L → 5–30 µL) |
| 2 | Yeast Extract | 100 mg/mL (100 g/L) | target_g_per_L / 100 × 200 µL | **OPTIMIZE** (2.5–25 g/L → 5–50 µL) |
| 3 | NaCl | 5M (292.2 g/mol) | target_mM / 5000 × 200 µL | Fixed 275 mM → 11 µL |
| 4 | Glucose | 100 mg/mL (100 g/L) | target_g_per_L / 100 × 200 µL | Fixed 0–2 g/L → 0–4 µL |
| 5 | MOPS 1M pH 7 | 1M | target_mM / 1000 × 200 µL | **OPTIMIZE** (25–150 mM → 5–30 µL) |
| 6 | MgSO₄ | 1M | target_mM / 1000 × 200 µL | Fixed 2 mM → 0.4 µL ⚠️ |
| 7 | CaCl₂ | 1M | target_mM / 1000 × 200 µL | **EXCLUDED** (precipitation) |
| 8 | FeSO₄ | 1M | target_mM / 1000 × 200 µL | **EXCLUDED** (oxidation at pH 7) |
| 9 | K₂HPO₄ | 1M | target_mM / 1000 × 200 µL | **EXCLUDED** (precipitation risk) |
| 10 | KH₂PO₄ | 1M | target_mM / 1000 × 200 µL | Fixed 10 mM → 2 µL ⚠️ |
| 11 | (NH₄)₂SO₄ | 1M | target_mM / 1000 × 200 µL | Excluded (redundant with YE/Tryptone) |
| 12 | KCl | 2M | target_mM / 2000 × 200 µL | Excluded |
| 13 | Sodium L-Glutamate | 1M | target_mM / 1000 × 200 µL | Excluded |
| 14 | Glycerol | 10% (v/v) | target_pct / 10 × 200 µL | Excluded |
| 15 | Sodium Citrate | 1M | target_mM / 1000 × 200 µL | Available as chelator if needed |
| 16 | HCl 12N / NaOH 10N | — | — | pH adjust only if needed |
| 17 | Trace metals | 1000× | 1/1000 × 200 = 0.2 µL ⚠️ | Fixed 1× — needs pre-dilution |

Remainder to 180 µL = sterile water. Then 20 µL cell inoculum added separately.

> **⚠️ Sub-pipettable volumes:** MgSO₄ (0.4 µL), KH₂PO₄ (2 µL), Trace metals (0.2 µL) are below the 5 µL accuracy threshold. **Action needed:** Ask Monomer to prepare a "mineral premix" or diluted working stocks before the run.

## Precipitation Constraints

| # | Limitation | Value |
|---|-----------|-------|
| PC1 | Core 5 stocks | No precipitation risk — can premix freely |
| PC2 | CaCl₂ + any phosphate (K₂HPO₄ or KH₂PO₄) | Immediate precipitate — never combine |
| PC3 | CaCl₂ + Novel Bio | Immediate precipitate — Novel Bio contains K₂HPO₄ (3 g/L) |
| PC4 | MgSO₄ + K₂HPO₄ | Precipitates above ~15 mM — use KH₂PO₄ instead |
| PC5 | MgSO₄ + K₂HPO₄ + Sodium Citrate ≥12.5 mM | Citrate chelates Mg²⁺, rescues this pair (add citrate first) |
| PC6 | MgSO₄ + KH₂PO₄ | Safe — no issue **⚠️ SEE PC13** |
| PC7 | FeSO₄ + K₂HPO₄ | Presumed incompatible (Ksp ≈ 10⁻³⁶) — treat like CaCl₂ |
| PC8 | FeSO₄ + KH₂PO₄ | Untested — use low concentration only, inspect visually |
| PC9 | Default phosphate rule | **Use KH₂PO₄ (monobasic) as default phosphate source** |
| PC10 | Addition order | See refined order below |
| PC11 | All defined pre-made media contain K₂HPO₄ | Defined-Minimal, Semi-Defined, High Buffer Defined, Defined-Glycerol — adding CaCl₂ or high MgSO₄ to any of these will precipitate |
| PC12 | Novel Bio contains both MgSO₄ (33 mM) and K₂HPO₄ | Works in practice (possibly Tris buffer chelation) — do not assume this generalizes to custom mixes |
| PC13 | **KH₂PO₄ at pH 7 behaves like K₂HPO₄** | When KH₂PO₄ hits MOPS buffer (pH 7), ~40% deprotonates to HPO₄²⁻ — precipitates with Ca²⁺ and Mg²⁺ just as aggressively. Keep divalent cations < 1-2 mM if using MOPS + phosphate. |
| PC14 | **CaCl₂ + Sulfate sources** | CaSO₄ is sparingly soluble (Ksp ≈ 4.9×10⁻⁵). If total SO₄²⁻ > 50 mM, Ca²⁺ must be < 1 mM. |
| PC15 | **CaCl₂ + Sodium Citrate** | Calcium citrate is highly insoluble (Ksp ≈ 5×10⁻¹⁸). Citrate rescues Mg but precipitates Ca — never combine. |
| PC16 | **FeSO₄ at pH 7** | Fe²⁺ oxidizes to Fe³⁺ at neutral pH → Fe(OH)₃ precipitate (Ksp ≈ 2.8×10⁻³⁹). Any FeSO₄ at pH 7 will rust out. |
| PC17 | **FeSO₄ safe threshold at pH 7** | If must use: ≤ 10 µM with Sodium Citrate as weak chelator. Without citrate, virtually zero solubility. |

### Refined Addition Order for Opentrons Flex

To prevent local concentration spikes during mixing, add stocks in this order:

1. **Water/Diluent** (provides max starting volume)
2. **Core organics & salts:** Tryptone, YE, Glucose, Glycerol, NaCl, KCl, Na-Glutamate, (NH₄)₂SO₄
3. **Buffer:** MOPS 1M pH 7
4. **Chelator:** Sodium Citrate (must be present before divalent cations)
5. **Phosphate:** KH₂PO₄
6. **Trace Metals**
7. **Divalent Cations (LAST):** MgSO₄, then FeSO₄, then CaCl₂

### Precipitation Detection (No Chemical Indicators)

Measure OD600 of all wells **immediately after mixing, BEFORE adding cells**:
- Clear media: OD600 ~0.00–0.05
- Precipitated: OD600 > 0.10 → flag as failed formulation, exclude from growth analysis

## Biological Constraints

| # | Limitation | Value |
|---|-----------|-------|
| B1 | Organism | V. natriegens (marine halophile, requires Na⁺) |
| B2 | Lab strain | Novel Media Strain (modified to over-produce plasmids) |
| B3 | Growth temperature | 30–37°C (optimal 37°C) |
| B4 | pH optimum | 7.0–7.5. Note: Novel Bio NBxCyclone is pH 6.4 — below optimum |
| B5 | NaCl is required | Cannot go below ~85 mM / 0.5% (growth ceases) |
| B6 | Lag phase after media switch | 15–90+ min — not indicative of toxicity |
| B7 | Inoculum must be pre-adapted | Mid-log phase in LBv2 before plating |
| B8 | Target inoculation OD | ~0.05 per well |
| B9 | Inoculum volume | 20 µL per well (from cell culture stock plate) |

## Optimizer Constraints

| # | Limitation | Value |
|---|-----------|-------|
| O1 | Optimizer | BayBE (Bayesian optimization) |
| O2 | Batch size | 10 (matches plate layout) |
| O3 | Noise floor guard | Do not feed data where max corrected OD < 0.1 |
| O4 | Lag phase guard | If all µ < 0.5 hr⁻¹, extend incubation — do not feed to BayBE |
| O5 | Positive control required | Basal media on every plate |

## Operational Constraints

| # | Limitation | Value |
|---|-----------|-------|
| OP1 | Reagent layout doc required | Share Google Doc with carter@monomerbio.com explaining reagent plate layout |
| OP2 | Monomer staff prepares stock plate | Pre-filled 24-well deep well with known reagent stocks |
| OP3 | Monomer can prepare 2 composed media | Between rounds, plus dilutions of existing stocks |
| OP4 | Stock plate modifiable between rounds | Can add/replace solutions if precipitation occurs |
| OP5 | 37°C incubator available | Liconic STX-220 |
| OP6 | 4°C incubator available | Liconic STX-110 (cold storage) |
| OP7 | Carousel available | Liconic LPX-220 (plate staging) |
| OP8 | Robotic arm | KX-2 (plate transport between instruments) |

## Pre-Made Media Reference

# Pre-Built Media Collection

## 1. Novel Bio NBxCyclone Media

**Description:** NBx CyClone™ Growth Media — Optimized for rapid plasmid production in *V. natriegens*.

- **Stock Solution Concentration:** N/A
- **Link to Product:** [BioRxiv Paper](https://www.biorxiv.org/)
- **SDS:** —
- **pH:** 6.4

### Composition

| Component | Concentration |
|---|---|
| Yeast extract | 15 g/L |
| Vegetable tryptone | 2.5 g/L |
| Magnesium sulfate (anhydrous) | 4 g/L |
| Sodium chloride | 22.5 g/L |
| Dipotassium phosphate (K₂HPO₄) | 3 g/L |
| Tris buffer | 150 mM |

### Notes

- Sterilize via 0.2 µm filtration (not autoclaving)
- Animal-free formulation (vegetable-derived tryptone)

---

## 2. Prepared LBv2 Media

- **Stock Solution Concentration:** —
- **Link to Product:** —
- **SDS:** —

### Composition

| Stock Solution | Final Concentration |
|---|---|
| Sterile Water | — |
| NaCl (5 M) | 375 mM |
| Tryptone (100 mg/mL) | 10 mg/mL |
| Yeast Extract (100 mg/mL) | 5 mg/mL |
| KCl (2 M) | 4 mM |
| MgSO₄ (1 M) | 2 mM |

---

## 3. Defined-Minimal Media

- **Stock Solution Concentration:** —
- **Link to Product:** —
- **SDS:** —

### Composition

| Stock Solution | Final Concentration |
|---|---|
| Sterile Water | — |
| NaCl (5 M) | 275 mM |
| MOPS pH 7 (1 M) | 40 mM |
| K₂HPO₄ (1 M) | 1 mM |
| (NH₄)₂SO₄ (1 M) | 10 mM |
| Glucose (100 mg/mL) | 2 mg/mL (0.2%) |
| Trace metals (1000×) | 1× |
| MgSO₄ (1 M) | 1 mM |

---

## 4. Semi-Defined Media

- **Stock Solution Concentration:** —
- **Link to Product:** —
- **SDS:** —

### Composition

| Stock Solution | Final Concentration |
|---|---|
| Sterile Water | — |
| NaCl (5 M) | 275 mM |
| MOPS pH 7 (1 M) | 40 mM |
| K₂HPO₄ (1 M) | 4 mM |
| KH₂PO₄ (1 M) | 1 mM |
| (NH₄)₂SO₄ (1 M) | 10 mM |
| Glucose (100 mg/mL) | 2 mg/mL (0.2%) |
| Tryptone (100 mg/mL) | 5 mg/mL |
| Yeast Extract (100 mg/mL) | 2.5 mg/mL |
| Trace metals (1000×) | 1× |
| MgSO₄ (1 M) | 1 mM |

---

## 5. High Buffer Defined Media

- **Stock Solution Concentration:** —
- **Link to Product:** —
- **SDS:** —

### Composition

| Stock Solution | Final Concentration |
|---|---|
| Sterile Water | — |
| NaCl (5 M) | 275 mM |
| MOPS pH 7 (1 M) | 100 mM |
| K₂HPO₄ (1 M) | 4 mM |
| KH₂PO₄ (1 M) | 1 mM |
| (NH₄)₂SO₄ (1 M) | 20 mM |
| Glucose (100 mg/mL) | 4 mg/mL (0.4%) |
| Trace metals (1000×) | 1× |
| MgSO₄ (1 M) | 1 mM |

---

## 6. Defined-Glycerol

- **Stock Solution Concentration:** —
- **Link to Product:** —
- **SDS:** —

### Composition (for 9 mL total volume)

| Stock Solution | Volume | Final Concentration |
|---|---|---|
| Sterile Water | 7.0 mL | — |
| K₂HPO₄ (1 M) | 36 µL | 4 mM |
| KH₂PO₄ (1 M) | 9 µL | 1 mM |
| (NH₄)₂SO₄ (1 M) | 90 µL | 10 mM |
| Glycerol (neat) | 28 µL | 0.4% (w/v) |
| Trace metals (1000×) | 9 µL | 1× |
| MgSO₄ (1 M) | 9 µL | 1 mM |

---

## Summary

| # | Media | Purpose |
|---|---|---|
| 1 | Novel Bio NBxCyclone | Specialized for *V. natriegens* plasmid production |
| 2 | Prepared LBv2 | Modified LB with enhanced salt content |
| 3 | Defined-Minimal | Basic defined media with glucose as carbon source |
| 4 | Semi-Defined | Defined components + tryptone/yeast extract |
| 5 | High Buffer Defined | Enhanced buffering (increased MOPS) |
| 6 | Defined-Glycerol | Defined media with glycerol as carbon source |


### Reference Concentration Ranges Across All Pre-Made Media

| Component | Min | Max | Notes |
|-----------|-----|-----|-------|
| NaCl | 275 mM (16 g/L) | 385 mM (22.5 g/L) | Our SS3 upper bound of 35 g/L (600 mM) exceeds all references |
| MOPS | 40 mM | 100 mM | Not in LBv2 or Novel Bio |
| MgSO₄ | 1 mM | 33 mM | Wide range; Novel Bio is an outlier at 33 mM |
| K₂HPO₄ | 1 mM | 4 mM | Present in all defined media — precipitation risk with divalent cations |
| KH₂PO₄ | 0 mM | 1 mM | Only in Semi-Defined and High Buffer Defined |
| Glucose | 0.2% (2 g/L) | 0.4% (4 g/L) | Our SS4 upper bound of 20 g/L is 5–10× higher than references |
| Yeast Extract | 2.5 g/L | 15 g/L | Our SS5 range (2–10 g/L) is reasonable |
| Tryptone | 2.5 g/L | 10 g/L | Fixed at 10 g/L in our setup |
