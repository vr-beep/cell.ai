# V. natriegens Media Optimization Strategy

**Purpose:** Reference guide for hackathon media formulation decisions
**Date:** 2026-03-14
**Source:** Elnora agent consultation

---

## 1. Component Selection

**Optimizing:** NaCl, Yeast Extract, Glucose (3 factors)
**Fixed:** Tryptone at 10 g/L, MOPS pH 7

### Why these three

- **NaCl** — *V. natriegens* is a halophile; salt concentration is the most critical physical parameter for growth rate.
- **Glucose** — provides raw carbon/energy for rapid exponential growth. *V. natriegens* has extraordinarily high glycolytic flux (up to 3.90 g/g/h aerobically).
- **Yeast Extract** — supplies osmoprotectants (glycine betaine), vitamins, and peptides to help cells handle osmotic stress from high salt and sugar.

### Why NOT others

Tryptone and Yeast Extract are complex biologicals already containing significant phosphates, magnesium, calcium, and trace metals. Adding supplemental MgSO₄, phosphates, or trace metals to rich media usually yields diminishing returns and risks toxicity or precipitation.

---

## 2. Concentration Ranges

| Component     | Range         | Notes |
|---------------|---------------|-------|
| NaCl          | 10–30 g/L     | ~170–510 mM. Below 10 starves sodium; above 30 increases osmotic stress without benefit. |
| Glucose       | 5–20 g/L      | Cells won't deplete 20 g/L in 3 hrs, but higher initial concentration increases glycolytic flux. At 20 g/L, glucose stock uses 20% of well volume — plan liquid handling accordingly. |
| Yeast Extract | 2–10 g/L      | Standard is 5 g/L. Pushing to 10 tests if excess vitamins/peptides boost μ_max. |

---

## 3. Optimization Strategy: BayBE over DOE

**Use Bayesian Optimization (BayBE), not traditional DOE.**

With only 14 conditions per round, traditional DOE is too rigid. A 3-factor Box-Behnken design requires 15 runs just for Round 1, leaving no room to iterate.

**BayBE approach:**
- **Round 1:** 14 conditions as space-filling initialization (Latin Hypercube sampling) across the 3D parameter space.
- **Feed** OD600 results into the Bayesian model.
- **Round 2:** Gaussian Process surrogate model balances *exploration* (uncertain areas) and *exploitation* (highest OD600 zones).

---

## 4. Precipitation Risks

### Critical rule
**Never mix K₂HPO₄ (dibasic) with MgSO₄ or CaCl₂.**

They form insoluble magnesium phosphate or calcium phosphate precipitates that:
- Ruin OD600 readings (precipitate scatters light → false cell growth signal)
- Starve cells of nutrients

### Fix
If adding a phosphate source later, **always use KH₂PO₄ (monobasic)** — safe and compatible with all divalent cations (Mg²⁺, Ca²⁺).

---

## 5. Carbon Source: Glucose over Glycerol

**Stick with glucose.** *V. natriegens* achieves its ~10 min doubling time via massive glucose consumption. Glycerol enters metabolism lower down (as DHAP) and yields slower μ_max.

Glycerol is only preferred in multi-day fed-batch fermentations to prevent acetate toxicity from overflow metabolism — irrelevant in a 3-hour assay.

---

## 6. Liquid Handling: Order of Operations

Follow: **Diluent → Buffer → Organics → Divalent cations last**

For 1 mL final volume per well:

| Step | Component | Rationale |
|------|-----------|-----------|
| 1 | Water | Bulk volume for instant dilution of concentrated stocks |
| 2 | MOPS pH 7 (1M) | Establishes buffering capacity immediately |
| 3 | NaCl (5M) | Disperses easily into buffered water |
| 4 | Tryptone & Yeast Extract (100 mg/mL) | Complex organics |
| 5 | Glucose (100 mg/mL) | After nitrogen sources |
| 6 | Phosphates (if used) | e.g., KH₂PO₄ |
| 7 | Divalent cations (if used) | MgSO₄ and CaCl₂ **always last** — prevents localized concentration spikes |

---

## 7. Master Mix Strategy

### Why master mix is required
Pipetting all components individually into 14 conditions × 4 wells exceeds the ~42 transfers/routine limit of the hackathon workcell.

### Recommended master mix
Pre-combine in a reservoir:
- Sterile water (calculated for remaining volume)
- MOPS pH 7 (to final fixed concentration, e.g., 50 mM)
- Tryptone (fixed at 10 g/L)

**Robot then does:** 1 master mix transfer per well + 3 variable spikes (NaCl, Glucose, YE).

---

## 8. Precipitation Compatibility Matrix

| Stock A | Stock B | Safe? | Notes |
|---------|---------|-------|-------|
| Tryptone + YE + NaCl + Glucose + MOPS | Any combination | Yes | Fully compatible even at stock concentrations |
| K₂HPO₄ (1M) | MgSO₄ (1M) | **NO** | Instant magnesium phosphate precipitate |
| K₂HPO₄ (1M) | CaCl₂ (1M) | **NO** | Instant calcium phosphate precipitate |
| KH₂PO₄ (1M) | MgSO₄ / CaCl₂ | Yes | Monobasic phosphate is safe with divalent cations |

---

## 9. MOPS Buffer Placement

**MOPS must go in early** (ideally built into the master mix).

Yeast Extract and Tryptone have variable batch-to-batch pH. Adding concentrated 5M NaCl or organics to unbuffered water can cause localized pH spikes, crashing proteins in yeast extract (cloudiness). MOPS at pH 7 prevents this.

---

## 10. Robot Tips

- Calculate variable component volumes in **microliters (µL) as integers** — Monomer API rejects float values.
- Keep total transfers per routine under ~42.
- Budget ~45 min for protocol execution.
- Fresh plate per round.
