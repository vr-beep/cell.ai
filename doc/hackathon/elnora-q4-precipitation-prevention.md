# Elnora Q4: Precipitation Prevention in Automated Media Mixing

**Task ID:** `359c3ed6-784c-4b01-979a-62e88e2e9fb6`
**Date:** 2026-03-14
**Project:** Cell.ai - V.natriegens Media Optimization

## Question

What media components cause precipitation when combined, and is there a way to design against that in our automated workflow?

## Elnora Response

This is a classic and dangerous media formulation trap. Your current rules have a critical flaw regarding pH and phosphate that will likely cause your automated runs to fail if not corrected.

Here is a detailed breakdown of the precipitation risks you are missing and how to design your Opentrons Flex workflow to avoid them.

### 1. Other Incompatible Pairs You Are Missing
You have correctly identified the primary phosphate risks, but you are missing three major secondary risks:
*   **Calcium + Sulfate (CaSO4):** You have `CaCl2` and three sulfate sources (`MgSO4`, `(NH4)2SO4`, `FeSO4`). Calcium sulfate is sparingly soluble (Ksp ≈ 4.9×10⁻⁵).
*   **Calcium + Citrate:** Calcium citrate is highly insoluble (Ksp ≈ 5×10⁻¹⁸). While sodium citrate rescues magnesium, it will aggressively precipitate calcium.
*   **Iron + Oxygen/pH:** `FeSO4` contains Fe²⁺. At neutral pH (like your MOPS pH 7), Fe²⁺ rapidly oxidizes to Fe³⁺, which immediately precipitates as rust-colored Iron(III) hydroxide (Fe(OH)₃, Ksp ≈ 2.8×10⁻³⁹).

### 2. Concentration Thresholds for Dangerous Pairs
*   **Ca²⁺ + SO₄²⁻:** To stay below the Ksp, if your total sulfate is 50 mM (typical for `(NH4)2SO4` + `MgSO4`), your **Ca²⁺ must be kept strictly below 1 mM**.
*   **Ca²⁺ + Citrate:** If you use 12.5 mM Sodium Citrate to rescue magnesium, your **Ca²⁺ must be kept below 31 µM**. (Effectively, you cannot use Calcium and Citrate together).
*   **Fe²⁺ + PO₄³⁻:** At pH 7 with 50 mM total phosphate, the maximum soluble Fe²⁺ is **~0.05 µM**. Above this, Iron(II) phosphate (vivianite) precipitates.
*   **Fe³⁺ + OH⁻:** At pH 7, virtually **any** oxidized iron will precipitate.

### 3. Should You Include These in the Search Space?
**Exclude them entirely or heavily constrain them.**
*   **Exclude:** `CaCl2` + `Sodium Citrate` (never mix).
*   **Exclude:** `FeSO4` + `K2HPO4` (never mix).
*   **Constrain:** If using `MgSO4` or `(NH4)2SO4` > 10 mM, constrain `CaCl2` to < 1 mM.

### 4. Optimal Addition Order for the Liquid Handler
Your current rule ("buffer first, divalent cations last") is generally good, but needs refinement to prevent local concentration spikes in the unmixed well. The Opentrons should add stocks in this exact order:
1.  **Water/Diluent** (if applicable, to provide maximum starting volume)
2.  **Core Organics & Salts:** Tryptone, YE, Glucose, Glycerol, NaCl, KCl, Na-Glutamate, (NH4)2SO4
3.  **Buffer:** MOPS 1M pH 7
4.  **Chelator:** Sodium Citrate (must be present *before* Mg/Fe are added)
5.  **Phosphate:** KH2PO4
6.  **Trace Metals**
7.  **Divalent Cations (LAST):** MgSO4, then FeSO4, then CaCl2.
*(Note: By adding divalent cations last, they enter a fully diluted, buffered, and chelated environment, minimizing local supersaturation at the point of dispensing).*

### 5. Can Sodium Citrate Safely Expand the Component Set?
**Yes, but only for Magnesium, and at the cost of Calcium.**
Adding ≥12.5 mM Sodium Citrate will successfully chelate Mg²⁺ and prevent it from precipitating with K2HPO4. However, because Calcium Citrate is highly insoluble, using Citrate means you must drop `CaCl2` from that specific media formulation entirely.

### 6. The pH Trap: Why Your KH2PO4 Rule is Dangerous
You noted: *"Use KH2PO4 (monobasic) as default phosphate source."*
**This rule is only safe if the media remains acidic.**

KH2PO4 is safe at its natural pH (~4.5) because >99% of the molecules are in the H₂PO₄⁻ state, which does not precipitate with Ca²⁺ or Mg²⁺. However, you are adding **MOPS 1M pH 7**.

The moment KH2PO4 hits the MOPS buffer, the pH rises to 7. At pH 7, the phosphate deprotonates, and **~40% of it becomes HPO₄²⁻** (the exact same dangerous ion found in K2HPO4). Therefore, in a MOPS-buffered pH 7 solution, **KH2PO4 will precipitate with Calcium and Magnesium just as aggressively as K2HPO4.**
*Workaround:* Keep divalent cations very low (< 1-2 mM) if using MOPS + Phosphate.

### 7. Safe FeSO4 Concentrations with KH2PO4
If the final solution is unbuffered and remains at pH 4.5 (where KH2PO4 naturally sits), FeSO4 is safe up to standard supplementation levels (10–100 µM) because the PO₄³⁻ ion concentration is virtually zero. However, if you buffer to pH 7 with MOPS, FeSO4 will precipitate with the phosphate. If you must use FeSO4 at pH 7, keep it **≤ 10 µM** and ensure Sodium Citrate is present to act as a weak iron chelator.

### 8. In-Well Precipitation Indicators
**Do not add chemical indicators.** They can be toxic to *V. natriegens* or interfere with fluorescence assays.
Instead, leverage the hackathon's hardware: **Measure the OD600 of all plates immediately after the automated mixing finishes, BEFORE adding cells.**
*   A successful, clear media will have an OD600 of ~0.00 to 0.05.
*   Any well with an OD600 > 0.10 before inoculation has precipitated. You can programmatically flag these wells as "failed formulations" in your data pipeline and exclude them from growth analysis.
