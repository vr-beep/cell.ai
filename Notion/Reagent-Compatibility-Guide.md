---
notion_title: "Reagent Compatibility Guide"
notion_id: "ebe329f4-baac-83c8-88c0-01bfa8ec2f46"
exported: "2026-03-15"
---

# Reagent Compatibility Guide

**Precipitation safety for V. natriegens media optimization hackathon**
*Based on EXP-011, EXP-012, EXP-014, EXP-016 - March 2-12, 2026 - Carter Allen & Will Pierce*

---

## The Short Version

Some of your stock reagents form insoluble precipitates when combined. The problem pairs are **divalent cations (Ca2+, Mg2+, Fe2+) + dibasic phosphate (K2HPO4)**. Your monobasic phosphate (KH2PO4) is safe with everything tested.

**Use KH2PO4 as your default phosphate source and you won't have precipitation problems.**

---

## Compatibility Matrix

Your phosphate stocks are at their natural pH (not pH-adjusted). This is what determines compatibility.

|  | **K2HPO4** (nat. pH ~8.7) | **KH2PO4** (nat. pH ~4.5) | **Novel Bio** |
|---|---|---|---|
| **CaCl2** | Incompatible — no fix | Safe | Incompatible |
| **MgSO4** | Only with >=12.5 mM citrate | Safe | Safe |
| **FeSO4** | Presumed incompatible (untested) | Untested — use low conc. only | Presumed incompatible (untested) |

All other stock reagents (NaCl, KCl, (NH4)2SO4, glucose, glycerol, tryptone, yeast extract, MOPS, Na-glutamate, HCl, NaOH) are **safe to combine freely**.

> **Note:** Trace metals data was confounded by a 10x dilution error during testing. Interpret with caution if combining with divalent cations at high concentrations.

---

## Rules

### 1. Never combine CaCl2 with K2HPO4

Precipitates at all tested concentrations (down to 2.9 mM divalent against 50 mM phosphate). Cannot be rescued by sodium citrate, even at 50 mM. If you need calcium and phosphate in the same well, **use KH2PO4 instead**.

### 2. Never add CaCl2 to Novel Bio

Novel Bio contains phosphate. CaCl2 precipitates immediately on contact (OD600 up to 0.72 vs. 0.09 background). No workaround has been identified. Consider whether exogenous calcium is truly necessary in your formulation.

### 3. MgSO4 + K2HPO4 requires sodium citrate

If you must combine these, add **>=12.5 mM sodium citrate** to the well **before** the other reagents. Practical recipe for a 200 uL well: **2.5 uL of 1 M sodium citrate** provides 12.5 mM. Without citrate, this pair precipitates heavily above ~15 mM. The simpler alternative: **use KH2PO4 instead of K2HPO4**.

### 4. Treat FeSO4 like CaCl2 until tested

Iron(II) phosphate (vivianite) has an extremely low Ksp (~10^-36). FeSO4 + K2HPO4 should be assumed incompatible. FeSO4 + KH2PO4 at natural pH may work at low concentrations — inspect visually if you try it.

---

## Decision Flowchart

**Does your well contain a divalent cation (CaCl2, MgSO4, or FeSO4)?**

- **No** — All phosphate forms are safe. Use whichever you prefer.
- **Yes, CaCl2** — Use KH2PO4 only. Do not use K2HPO4 or Novel Bio.
- **Yes, MgSO4** — KH2PO4 is simplest (always safe). K2HPO4 works only with >=12.5 mM citrate added first.
- **Yes, FeSO4** — Use KH2PO4 at the lowest iron concentration you can. Avoid K2HPO4. Inspect visually.
- **Multiple divalents + phosphate** — KH2PO4 is the only option that works with all of them.

---

## Why This Happens

Divalent cations react with HPO4^2- (the dibasic phosphate ion) to form insoluble salts. The key reactions:

- Ca2+ + HPO4^2- -> CaHPO4 (Ksp ~ 2.7x10^-7)
- Mg2+ + HPO4^2- -> MgHPO4 (Ksp ~ 1.5x10^-6)

Whether precipitation occurs depends on **which phosphate species dominates**, which is controlled by pH:

- **KH2PO4 at natural pH (~4.5):** >99% H2PO4^- — this form does NOT precipitate with divalent cations at working concentrations. **This is why KH2PO4 is safe.**
- **K2HPO4 at natural pH (~8.7):** >90% HPO4^2- — this form precipitates readily. **This is why K2HPO4 is problematic.**
- **Either phosphate at pH 7:** ~60% HPO4^2- — both behave the same and both precipitate. This is why earlier experiments (which used pH 7-adjusted stocks) saw no difference between the two phosphate salts.

Your hackathon stocks are at natural pH, so the distinction between KH2PO4 (safe) and K2HPO4 (risky) holds. Only MOPS has been pH-adjusted (to 7.0); MOPS does not participate in precipitation.

**Sodium citrate** works by chelating free Mg2+/Ca2+, reducing the ion concentration below the precipitation threshold. This is sufficient for Mg2+ (whose phosphate salt is more soluble) but not for Ca2+ (whose phosphate Ksp is ~6x lower).

---

## Stock Reference

| Reagent | Stock Conc. | pH | Precip. Risk |
|---|---|---|---|
| Tryptone (Vegetable) | 100 mg/mL | Natural | None |
| Yeast Extract | 100 mg/mL | Natural | None |
| Glycerol | 10% | Natural | None |
| Glucose | 100 mg/mL | Natural | None |
| Sodium Chloride | 5 M | Natural | None |
| **Magnesium Sulfate** | **1 M** | **Natural** | **Risk with K2HPO4** |
| Potassium Chloride | 2 M | Natural | None |
| Ammonium Sulfate | 1 M | Natural | None |
| **K2HPO4 (dibasic)** | **1 M** | **~8.7** | **Risk with divalent cations** |
| KH2PO4 (monobasic) | 1 M | ~4.5 | Safe with all tested divalents |
| MOPS | 1 M | 7.0 (adj.) | None |
| **Calcium Chloride** | **1 M** | **Natural** | **Risk with K2HPO4 & Novel Bio** |
| Trace Metals | 1000x | Natural | Data confounded |
| HCl | 12 N | Acidic | None |
| NaOH | 10 N | Basic | None |
| Sodium Citrate | 1 M | Natural | Chelator — rescues Mg2++K2HPO4 |
| Na L-Glutamate | 1 M | Natural | Not tested; low risk expected |
| **FeSO4-7H2O** | **1 M** | **Natural** | **Untested — presume incompatible with K2HPO4** |
| Novel Bio NBxCyclone | N/A | N/A | Contains phosphate — no CaCl2 |
| Prepared LBv2 | N/A | N/A | Not tested |
