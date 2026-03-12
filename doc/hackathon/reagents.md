# Track A Reagent Database

**Source:** Hackathon reagent screenshot + Format PDF
**Cell type:** Vibrio natriegens (confirmed)
**Basal media:** LBv2 (shown in Monomer's Culture Monitor)

## Available Reagents (16 total)

| # | Reagent | Category | Notes |
|---|---|---|---|
| 1 | Tryptone | Nitrogen source | Primary protein source in LB media |
| 2 | Yeast Extract | Nitrogen source | Vitamins, amino acids, growth factors |
| 3 | Sodium Chloride (NaCl) | Salt | Required for V. natriegens (marine organism). Hard requirement, not optional. |
| 4 | Glucose | Carbon source | Primary carbon/energy source |
| 5 | Glycerol | Carbon source | Alternative carbon source |
| 6 | Magnesium Sulfate (MgSO4) | Trace metal/cofactor | Essential cofactor for many enzymes |
| 7 | Calcium Chloride (CaCl2) | Trace metal | Cell signaling, membrane stability |
| 8 | Potassium Phosphate Monobasic (KH2PO4) | Buffer/phosphate | Buffering + phosphate source |
| 9 | Potassium Phosphate Dibasic (K2HPO4) | Buffer/phosphate | Buffering + phosphate source |
| 10 | Ammonium Chloride (NH4Cl) | Nitrogen source | Inorganic nitrogen |
| 11 | Sodium Hydroxide (NaOH) | pH adjuster | Raises pH |
| 12 | Hydrochloric Acid (HCl) | pH adjuster | Lowers pH |
| 13 | Iron(III) Chloride (FeCl3) | Trace metal | Essential trace element |
| 14 | Manganese Sulfate (MnSO4) | Trace metal | Essential trace element |
| 15 | Zinc Sulfate (ZnSO4) | Trace metal | Essential trace element |
| 16 | Thiamine (Vitamin B1) | Vitamin | Growth factor |

*Note: Exact stock concentrations to be confirmed day-of from Monomer's reagent labels.*

## Precipitation Constraints (Known)

These combinations must be excluded from the BayBE search space:

| Combination | Precipitate | Rule |
|---|---|---|
| CaCl2 + KH2PO4/K2HPO4 | Calcium phosphate (insoluble) | Never combine high [Ca2+] with high [phosphate] |
| High MgSO4 + high pH (NaOH) | Magnesium hydroxide | Keep MgSO4 below threshold if pH > 8 |
| FeCl3 + high pH | Iron hydroxide | FeCl3 precipitates above pH ~7 |

## Candidate 3 Components to Optimize

The hackathon asks: "What 3 media components are most impactful?"

**Top candidates** (to be finalized during Phase 1 Research with scientist input):

| Priority | Component | Rationale |
|---|---|---|
| Likely | **Glucose** | Primary carbon source. Concentration directly affects growth rate. |
| Likely | **MgSO4** | Essential cofactor. Often rate-limiting in minimal/defined media. |
| Likely | **NaCl** | V. natriegens is a marine halophile. Optimal [NaCl] is critical (1-3% range). |
| Maybe | Tryptone or Yeast Extract | Nitrogen sources — but may be part of basal LBv2 already |
| Maybe | KH2PO4/K2HPO4 | Buffering capacity affects long-term growth |

**pH adjusters (HCl/NaOH)** are likely fixed parameters, not optimization variables.

**Final decision comes from Phase 1 Research + scientist input.**
