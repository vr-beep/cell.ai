# Vibrio natriegens: Biology, Media, and Measurement Reference

> Research compiled March 11, 2026. Sources cited inline.

---

## 1. Published Optimal Media Compositions

### LBv2 (standard community medium)
- LB-Miller + v2 salts: 204 mM NaCl, 4.2 mM KCl, 23.14 mM MgCl2
- Salts added *on top of* standard LB NaCl (~1%)
- Total NaCl ~3%
- Source: https://barricklab.org/twiki/bin/view/Lab/ProtocolsWorkingWithVibrioNatriegens

### LB3
- LB-Miller + 2% additional NaCl (3% total NaCl)
- Becoming standardized community medium

### BHIv2 / BHIN (fastest growth)
- Brain Heart Infusion (37 g/L) + 15 g/L NaCl
- **Fastest growth recorded: mu = 4.43 h-1 (9.4 min doubling)**
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC5666143/ (Hoffart et al. 2017)

### VN Minimal Medium (defined)
- (NH4)2SO4 5 g/L, NaCl 15 g/L, KH2PO4 1 g/L, K2HPO4 1 g/L, MgSO4 0.25 g/L, CaCl2 0.01 g/L, FeSO4 16.4 mg/L, MnSO4 10 mg/L, CuSO4 0.3 mg/L, ZnSO4 1 mg/L, NiCl2 0.02 mg/L
- Source: Hoffart et al. 2017

### Low-chloride defined medium (VN6/VN10)
- Replaces NaCl entirely with Na2HPO4, Na2SO4, Na3-citrate (total Na+ constant)
- Achieved OD600 of 21.6 in shake flask, 62.5 g/L biomass in fed-batch
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC10638117/ (Grotefeld et al. 2023)

**CRITICAL WARNING:** Do NOT store V. natriegens at 4C — the organism enters a viable-but-nonculturable state and cannot detoxify ROS at cold temperatures.

---

## 2. Growth Rate Data

| Medium | Growth rate (mu, h-1) | Doubling time | Source |
|--------|----------------------|---------------|--------|
| BHIN (complex, optimized) | 4.43 | 9.4 min | Hoffart 2017 |
| BHI original (Eagon 1962) | ~4.24 | 9.8 min | Historical |
| LB + 2.5% NaCl | ~3.05 | 13.6 min | Long et al. 2019 |
| Glucose minimal (M9+NaCl) | 1.70 | ~24 min | Long et al. 2017 |
| Glucose minimal (pH 8.0) | 1.97 | ~21 min | Oellinger et al. 2024 |
| Sucrose minimal | 1.79 | ~23 min | Hoffart 2017 |
| Fructose minimal | 1.51 | ~28 min | Hoffart 2017 |
| Glycerol minimal | 0.86 | ~48 min | Hoffart 2017 |

**Hackathon expectation:** In LBv2-based complex medium at 37C, expect ~10-14 min doubling. In 2-4 hour incubation, cells should reach easily measurable OD600 from a low inoculum.

---

## 3. NaCl Concentration Sensitivity

- **Optimal range:** 1.5-2.5% (15-25 g/L)
- 2.5% NaCl yielded highest final OD (1.021) in LB optimization (Long et al. 2019, https://www.biorxiv.org/content/10.1101/775437v1.full)
- 1.0% NaCl: "markedly slower growth"
- V. natriegens tolerates up to 100 g/L NaCl but growth inhibited above ~30 g/L
- **Cannot grow WITHOUT NaCl** (obligate halophile)
- Lower NaCl (7.5-15 g/L) optimal in MOPS-buffered defined media (Oellinger et al. 2024)
- Osmolality sweet spot: 1.0-1.6 Osmol/kg; above 2.0 Osmol/kg causes growth inhibition
- Na+, Mg2+, and K+ all required for enzyme induction

**For hackathon:** Scientist-defined range of 10-35 g/L covers the literature optimum. At 35 g/L, approaching upper osmolarity tolerance — watch for growth suppression at this boundary.

---

## 4. Glucose Utilization

**Yes, V. natriegens benefits substantially from glucose supplementation.**

- Glucose uptake rate: 3.90 g/g/h aerobic (**2x faster than E. coli**)
- Biomass yield on glucose: 0.44 gDW/g glucose
- Growth rate on glucose minimal: 1.70 h-1 (~24 min doubling)
- **Produces acetate as byproduct:** ~0.8 mol acetate per mol glucose consumed
- Among carbon sources: glucose, maltose, trehalose, and malate gave strongest growth

**Concentrations in literature:**
- 1.8 g/L (10 mM) in flux analysis studies
- 10-20 g/L in batch optimization
- 12 g/L in shake flask defined media
- 24 g/L in bioreactor batch phase

**CRITICAL WARNING:** Glucose produces acetate, which drops pH. Without buffering (MOPS), residual glucose and acetate remain unconsumed once pH falls to ~5.3. V. natriegens is notably sensitive to its own acidic fermentation products.

Sources:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5845447/ (Long et al. 2017)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11421182/ (Oellinger et al. 2024)

---

## 5. Yeast Extract Effects

Limited direct optimization data found. Standard concentrations:
- LB standard: 5 g/L (most common)
- Nutrient broth: 3 g/L
- Minimal media supplement: 0.05 g/L (trace, in 13C flux studies)

**No published dose-response study specifically titrating yeast extract for V. natriegens.** This makes it a genuinely novel optimization target for the hackathon — the effect is likely positive but uncharacterized systematically.

---

## 6. MOPS Buffer Usage

**MOPS is standard in defined/minimal media for V. natriegens, not typically in complex media (LB/BHI).**

Key findings from Oellinger et al. 2024:
- With 20 g/L glucose: minimum 300 mM MOPS needed (300-350 mM optimal)
- With 10 g/L glucose: 180 mM MOPS sufficient
- At pH 8.0 initial: 220-300 mM optimal range
- Recommended: 10 g/L NaCl + 450 mM MOPS + 20 g/L glucose

**Why MOPS matters:** Stabilizes pH, allowing V. natriegens to reuptake acetate after glucose depletion. Without adequate buffering, pH drops to ~5.3 and acetate accumulates toxically.

**MOPS pKa = 7.2.** Effective buffering range: pH 6.5-7.9. Scientists chose 1M stock, pH adjusted to 7.

**For hackathon:** Using MOPS as the fill-up solvent (up to ~800 µL per 1 mL mix) provides strong buffering, especially important when glucose is added.

---

## 7. OD600 Measurement Issues

### General Plate Reader Issues
- **Linear range:** OD600 proportional to cell count only up to ~0.4-1.0 OD in plate reader
- **Path length:** 96-well plate with 200 µL → ~0.56 cm (vs 1.0 cm in cuvette)
- **Plate reader OD ≠ spectrophotometer OD** — conversion factor typically ~2.5x
- **Calibration:** LUDOX CL-X (45% colloidal silica) can serve as inter-instrument standard
- Source: https://www.bmglabtech.com/en/howto-notes/how-to-optimise-od600-measurements/

### Location-Dependent Bias
- OD600 shows gradual changes along columns 2-11 of 96-well plates
- Recommend distributing replicates across plate, not grouping
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC5752254/

### V. natriegens-Specific
- **CDW = OD600 × 0.27** for exponentially growing cells (Hoffart 2017)
- Rod-shaped, 0.5-0.8 × 1.5-3.0 µm (similar to E. coli — standard OD correlations apply)
- At OD > 1 in plate reader, multiple scattering makes readings unreliable; dilute before measuring

### Practical Recommendations
- Use endpoint measurement after 2-4 hour incubation
- If OD > 0.8 in plate reader, dilute 2-4x and re-read
- Always subtract matched blank wells at same timepoint
- Blanks must contain IDENTICAL media composition (including glucose + NaCl which form particles)

---

## 8. Edge Effects in 96-Well Plates

Quantified data from Mansoury et al. 2021 (https://pmc.ncbi.nlm.nih.gov/articles/PMC8024881/):

| Well Position | Reduction in Activity vs. Center |
|--------------|----------------------------------|
| Corner wells | 26-34% |
| Outer row wells | 16-35% |
| Second row | 7-25% |
| Third row | 1-10% (usually not significant) |

**Root cause:** Differential evaporation — edge/corner wells are hotter, lose volume, concentrate solutes.

**Mitigation (ranked by effectiveness):**
1. Fill outer wells with water/PBS as humidity buffer (sacrifice outer ring — most common)
2. Seal plates with breathable membrane or loose wrap
3. Pre-incubate at room temp 15-60 min before 37C (reduces thermal gradient)
4. Randomize replicate positions across plate
5. Maintain incubator humidity >95%

**For hackathon (2-4h incubation):** Edge effects will be moderate-to-significant. Filling outer ring with buffer and using only inner 60 wells is essential.

---

## 9. Blank Well Subtraction Protocol

**Standard protocol (Barrick Lab, https://barricklab.org/twiki/bin/view/Lab/ProtocolsGrowthRates):**

1. Include minimum 3 replicate blank wells per media type (uninoculated, same volume: 200 µL)
2. Blanks must contain **identical** media composition (including supplements)
3. Average blank OD600 at each timepoint
4. Subtract averaged blank from all sample wells at corresponding timepoint
5. Use per-media blanks (not a single plate blank) when testing multiple compositions

**Best practices:**
- Place blanks distributed across plate, not grouped, to account for positional bias
- For endpoint: subtract time-matched blank (media may change OD during incubation)
- Wells with bacteria should show net positive OD after blank subtraction at T=0; negative values indicate inoculum was too dilute

**For hackathon:** The scientist sync confirmed 1 blank per condition (4 wells per condition: 3 reps + 1 blank). Ideally we'd want 3 blanks per condition for statistical power, but with 60 wells and 14 conditions this isn't feasible. The single blank approach is a practical compromise.

---

## 10. Published BO/DOE Studies on V. natriegens

**No published Bayesian optimization or DOE study specifically optimizing V. natriegens media composition was found.** This makes the hackathon project **genuinely novel**.

Closest published work:
- Oellinger et al. 2024: Systematic but traditional one-factor-at-a-time optimization of V. natriegens in defined media
- A genome-scale metabolic model exists and has been used with metaheuristic optimization algorithms
- Turco et al. 2024/2025: BO for cell culture media (not V. natriegens) — achieved 3-30x fewer experiments than DOE

---

## 11. Key Biological Insights for BayBE Configuration

1. **NaCl and glucose interact via osmolarity** — high NaCl + high glucose may cause osmotic stress
2. **Glucose and pH interact** — glucose produces acetate, dropping pH; MOPS buffer mitigates this
3. **Yeast extract provides nitrogen + vitamins** — diminishing returns expected above ~8-10 g/L
4. **Expect growth rates of 2-4 h-1** in optimized complex media (mu = ln(2)/doubling_time)
5. **Growth rate from endpoint:** mu = ln(OD_corrected_final / OD_initial) / time_hours
6. **Starting OD for inoculation:** Typically OD600 = 0.05 (20 µL of OD 0.5 culture into 180 µL media)
