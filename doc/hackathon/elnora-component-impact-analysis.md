# V. natriegens Media Component Impact Analysis

**Source:** Elnora AI Agent (task `b84a6454-b932-4c5c-b881-fd03368c94be`)
**Date:** 2026-03-14

## Summary Matrix

| Medium | Component 1 | Range | Component 2 | Range | Component 3 | Range |
|---|---|---|---|---|---|---|
| **1. NBxCyclone** | MgSO₄ | 0.5–4.0 g/L | K₂HPO₄ | 1.0–10.0 g/L | Vegetable Tryptone | 2.5–15.0 g/L |
| **2. LBv2** | NaCl | 200–500 mM | Yeast Extract | 5–15 mg/mL | MgSO₄ | 1–10 mM |
| **3. Defined-Minimal** | K₂HPO₄ | 1–10 mM | MOPS pH 7 | 40–100 mM | Glucose | 1–5 mg/mL |
| **4. Semi-Defined** | MOPS pH 7 | 40–150 mM | Glucose | 0–4 mg/mL | Yeast Extract | 1–5 mg/mL |
| **5. High Buffer Defined** | (NH₄)₂SO₄ | 5–30 mM | MgSO₄ | 1–5 mM | K₂HPO₄ | 4–15 mM |
| **6. Defined-Glycerol** | K₂HPO₄ | 10–50 mM | Glycerol | 0.2–1.0% | (NH₄)₂SO₄ | 5–20 mM |

## Key Themes Across Media

- **Phosphorus (K₂HPO₄)** — appears in 5 of 6 media as critical; V. natriegens allocates massive biomass to RNA/ribosomes
- **Buffering (MOPS)** — critical in defined/semi-defined media due to acetate overflow metabolism
- **MgSO₄** — ribosome stability factor, appears in 3 of 6 media
- **NaCl/osmolarity** — marine organism, sensitive to osmolarity shifts

## Critical Warnings

1. **Media 6 (Defined-Glycerol) is missing NaCl** — V. natriegens will lyse without sodium. Must add ~275 mM NaCl.
2. **Media 1 (NBxCyclone) precipitation risk** — K₂HPO₄ + MgSO₄ at these concentrations may precipitate. pH 6.4 is suboptimal (prefer 7.0–7.5).

## BayBE Recommendation

Include terminal pH as a secondary objective/constraint alongside OD600/doubling time to prevent optimizing toward "fast but crashing" formulations.

## Full Analysis

### Media 1: Novel Bio NBxCyclone (pH 6.4, filter-sterilized)

1. **MgSO₄ (0.5–4.0 g/L)** — 4 g/L is unusually high, risks precipitation with K₂HPO₄. Need to find threshold for ribosome stability without crashing phosphate.
2. **K₂HPO₄ (1.0–10.0 g/L)** — Phosphorus heavily demanded for rRNA synthesis. Balance P supply against Mg²⁺ precipitation.
3. **Vegetable Tryptone (2.5–15.0 g/L)** — Current ratio heavily skewed toward YE (15 g/L) over Tryptone (2.5 g/L). Balancing amino acids vs vitamins/traces is a classic optimization vector.

### Media 2: Prepared LBv2

1. **NaCl (200–500 mM)** — Marine organism, highly osmolarity-sensitive. 375 mM is standard but optimal shifts with aeration/temperature.
2. **Yeast Extract (5–15 mg/mL)** — Provides critical growth factors bypassing biosynthetic bottlenecks. Directly correlates with μ_max.
3. **MgSO₄ (1–10 mM)** — Ribosome stability. 2 mM standard but ultra-fast growth may require more.

### Media 3: Defined-Minimal

1. **K₂HPO₄ (1–10 mM)** — 1 mM is severely limiting for fast-growing V. natriegens with high RNA content.
2. **MOPS pH 7 (40–100 mM)** — 40 mM often insufficient to buffer acetate overflow metabolism.
3. **Glucose (1–5 mg/mL)** — Balance max growth rate against acetate accumulation.

### Media 4: Semi-Defined

1. **MOPS pH 7 (40–150 mM)** — With glucose + complex nutrients, metabolic rate is extreme. 40 mM MOPS crashes quickly.
2. **Glucose (0–4 mg/mL)** — With tryptone/YE present, high glucose triggers catabolite repression or accelerates acetate overflow.
3. **Yeast Extract (1–5 mg/mL)** — Growth accelerator in minimal media. Optimize minimal required amount.

### Media 5: High Buffer Defined

1. **(NH₄)₂SO₄ (5–30 mM)** — 20 mM is high. Optimize C:N balance without ammonia toxicity.
2. **MgSO₄ (1–5 mM)** — High biomass yield may make 1 mM Mg²⁺ limiting for translation machinery.
3. **K₂HPO₄ (4–15 mM)** — May still bottleneck at high-density growth with 0.4% glucose.

### Media 6: Defined-Glycerol

⚠️ **Missing NaCl — must add ~275 mM**

1. **K₂HPO₄ (10–50 mM)** — Phosphate is the ONLY buffer (no MOPS). 5 mM total is completely inadequate.
2. **Glycerol (0.2–1.0%)** — Bypasses some overflow metabolism vs glucose. Needs concentration tuning for redox balance.
3. **(NH₄)₂SO₄ (5–20 mM)** — Primary nitrogen source, must couple to glycerol concentration for C:N ratio.
