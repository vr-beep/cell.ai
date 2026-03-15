# Track A: Develop an Agentic Closed Loop Workflow to Optimize Media Composition

## Overview

Build an autonomous workflow using Monomer's MCP to iteratively vary media components, generate growth curves, measure outcome using a platereader, and update the next experiment end-to-end — all on REAL cells. Integrate with Elnora's CLI/MCP to fully close the loop on deciding what media formulation to try next.

**Track A Leads:** Carter Allen / Carmen Kivisild

---

## Phase 1: Plan

Develop a game plan by reviewing the biology of Vibrio Natriegens, surveying the literature, and studying best practices using Elnora.

**Key Questions to Address:**
- What 3 media components in each of the pre-built media are most impactful to optimize?
- What dilution ranges should we try?
- Is a DOE appropriate or a different strategy given the limitations of the experimental setup?
- What media components cause precipitation and is there a way to design against that?

---

## Phase 2: Build

### Two Steps

1. **Tutorial of Monomer's System (1 hour):** Monomer Staff will walk both teams through running the same experiment to determine optimal seeding density of Vibrio Natriegens on the workcell.
2. **Experimental Execution (24 hours):** From what you learned using Elnora, and now with familiarity of the system, you will design iterative experiments to BUILD THE BEST MEDIA. Monomer will provide components and coaching for both teams using the resources available at Monomer HQ.

---

## Vibrio Natriegens Background

Vibrio natriegens is the fastest-growing non-pathogenic bacterium known, with a doubling time of ~10 minutes under optimal conditions — roughly 2-3x faster than E. coli. It is a marine gammaproteobacterium, facultative anaerobe, and BSL-1 organism.

**Lab strain:** Novel Media Strain (modified to over-produce plasmids)

### Key Growth Parameters
- **Optimal temperature:** 30-37°C
- **pH optimum:** 7.0-7.5
- **Requires NaCl** — halophile, typical lab range 0.5-2% NaCl (85-340 mM)
- **Doubling time:** ~10 min (rich media, 37°C) to ~30 min (defined minimal media)

### Defined Media Components

| Component | Role | Working Concentration |
|-----------|------|----------------------|
| NaCl | Osmolarity / halophile requirement | 85-340 mM (1-4 µL of 5M in 180 µL) |
| MOPS (pH 7) | Buffering | 20-40 mM |
| K₂HPO₄ / KH₂PO₄ | Phosphate source + secondary buffer | 2-10 mM |
| MgSO₄ | Essential cofactor | 0.5-2 mM |
| (NH₄)₂SO₄ | Nitrogen source | 5-20 mM |
| Glucose or Glycerol | Carbon source | 0.1-0.5% (w/v) |
| CaCl₂ | Trace structural / enzyme cofactor | 0.05-0.2 mM |
| Trace Metals (1000x) | Micronutrients | 1x final |

> **Critical:** Sodium is the single most important salt — V. natriegens will grow poorly or not at all without Na⁺.

### Key Papers
- **Eagon (1962)** — Original characterization; established ~10 min doubling time. J. Bacteriol. 83:736-737.
- **Weinstock et al. (2016)** — Established as a synthetic biology chassis. Nature Methods 13:849-851.
- **Tschirhart et al. (2019)** — Gene expression toolbox and defined media optimization. ACS Synthetic Biology 8(9):2069-2079.
- **Dalia et al. (2017)** — CRISPR-based genome editing tools. Genetics 207(4):1469-1480.

---

## Reagent Database

| Component | Stock Solution Concentration |
|-----------|------------------------------|
| Tryptone (Vegetable) | 100 mg/mL |
| Yeast Extract | 100 mg/mL |
| Glycerol | 10% in Sterile H₂O |
| Glucose | 100 mg/mL |
| Sodium Chloride | 5 M |
| Magnesium Sulfate | 1 M |
| Potassium Chloride | 2 M |
| Ammonium Sulfate | 1 M |
| Potassium Phosphate (dibasic) | 1 M |
| Potassium Phosphate (monobasic) | 1 M |
| MOPS (pH adjusted to 7) | 1 M |
| Calcium Chloride | 1 M |
| Trace metals solution | 1000X |
| HCl | 12 N |
| NaOH | 10 N |
| Sodium Citrate | 1 M |
| Sodium L-Glutamate Monohydrate | 1 M |
| Iron(II) sulfate heptahydrate | 1 M |
| Novel Bio NBxCyclone Media | N/A |

**Pre-made media also available:** Prepared LBv2, Defined-Minimal, Semi-Defined, High Buffer Defined, Defined-Glycerol.

---

## Reagent Compatibility Guide

*Based on EXP-011, EXP-012, EXP-014, EXP-016 · March 2-12, 2026 · Carter Allen & Will Pierce*

### The Short Version

Some stock reagents form insoluble precipitates when combined. The problem pairs are divalent cations (Ca²⁺, Mg²⁺, Fe²⁺) + dibasic phosphate (K₂HPO₄). Monobasic phosphate (KH₂PO₄) is safe with everything tested.

**Use KH₂PO₄ as your default phosphate source and you won't have precipitation problems.**

### Compatibility Matrix

| | K₂HPO₄ (nat. pH ~8.7) | KH₂PO₄ (nat. pH ~4.5) | Novel Bio |
|---|---|---|---|
| CaCl₂ | ❌ Incompatible — no fix | ✅ Safe | ❌ Incompatible |
| MgSO₄ | ⚠️ Only with ≥12.5 mM citrate | ✅ Safe | ✅ Safe |
| FeSO₄ | ❌ Presumed incompatible (untested) | ⚠️ Untested — use low conc. only | ❌ Presumed incompatible (untested) |

All other stock reagents (NaCl, KCl, (NH₄)₂SO₄, glucose, glycerol, tryptone, yeast extract, MOPS, Na-glutamate, HCl, NaOH) are safe to combine freely.

### Rules

1. **Never combine CaCl₂ with K₂HPO₄** — Precipitates at all tested concentrations. Cannot be rescued by sodium citrate. Use KH₂PO₄ instead.
2. **Never add CaCl₂ to Novel Bio** — Novel Bio contains phosphate. CaCl₂ precipitates immediately on contact.
3. **MgSO₄ + K₂HPO₄ requires sodium citrate** — Add ≥12.5 mM sodium citrate before other reagents. Practical: 2.5 µL of 1 M sodium citrate in a 200 µL well provides 12.5 mM. The simpler alternative: use KH₂PO₄.
4. **Treat FeSO₄ like CaCl₂ until tested** — FeSO₄ + K₂HPO₄ should be assumed incompatible.

### Decision Flowchart

- **No divalent cation?** → All phosphate forms are safe.
- **CaCl₂?** → Use KH₂PO₄ only. No K₂HPO₄ or Novel Bio.
- **MgSO₄?** → KH₂PO₄ is simplest (always safe). K₂HPO₄ works only with ≥12.5 mM citrate added first.
- **FeSO₄?** → Use KH₂PO₄ at the lowest iron concentration you can. Avoid K₂HPO₄. Inspect visually.
- **Multiple divalents + phosphate?** → KH₂PO₄ is the only option that works with all of them.

### Why This Happens

Divalent cations react with HPO₄²⁻ (the dibasic phosphate ion) to form insoluble salts:
- Ca²⁺ + HPO₄²⁻ → CaHPO₄↓ (Ksp ≈ 2.7×10⁻⁷)
- Mg²⁺ + HPO₄²⁻ → MgHPO₄↓ (Ksp ≈ 1.5×10⁻⁶)

KH₂PO₄ at natural pH (~4.5) has >99% H₂PO₄⁻ which does NOT precipitate. K₂HPO₄ at natural pH (~8.7) has >90% HPO₄²⁻ which precipitates readily. Sodium citrate works by chelating free Mg²⁺/Ca²⁺ below the precipitation threshold.

### Stock Reference Table

| Reagent | Stock Conc. | pH | Precip. Risk |
|---------|------------|-----|-------------|
| Tryptone (Vegetable) | 100 mg/mL | Natural | None |
| Yeast Extract | 100 mg/mL | Natural | None |
| Glycerol | 10% | Natural | None |
| Glucose | 100 mg/mL | Natural | None |
| Sodium Chloride | 5 M | Natural | None |
| Magnesium Sulfate | 1 M | Natural | ⚠️ Risk with K₂HPO₄ |
| Potassium Chloride | 2 M | Natural | None |
| Ammonium Sulfate | 1 M | Natural | None |
| K₂HPO₄ (dibasic) | 1 M | ~8.7 | ⚠️ Risk with divalent cations |
| KH₂PO₄ (monobasic) | 1 M | ~4.5 | ✅ Safe with all tested divalents |
| MOPS | 1 M | 7.0 (adj.) | None |
| Calcium Chloride | 1 M | Natural | ⚠️ Risk with K₂HPO₄ & Novel Bio |
| Trace Metals | 1000× | Natural | Data confounded |
| HCl | 12 N | Acidic | None |
| NaOH | 10 N | Basic | None |
| Sodium Citrate | 1 M | Natural | ✅ Chelator — rescues Mg²⁺+K₂HPO₄ |
| Na L-Glutamate | 1 M | Natural | Not tested; low risk expected |
| FeSO₄·7H₂O | 1 M | Natural | ⚠️ Untested — presume incompatible with K₂HPO₄ |
| Novel Bio NBxCyclone | N/A | N/A | ⚠️ Contains phosphate — no CaCl₂ |
| Prepared LBv2 | N/A | N/A | Not tested |

---

## Monomer Workcell

### Instrument List
- Opentrons Flex Liquid handler
- Liconic LPX-220 Carousel
- Liconic STX-110 4C Incubator
- Liconic STX-220 37C Incubator
- Tecan Infinite Platereader
- KX-2 Robotic Arm

---

## Labware Database

| Labware | Max Volume per Well |
|---------|-------------------|
| Lichen Cottage 24 Well Plate with Lid | 2.2 mL |
| CellPro 10.4ml 24-Well Deep Well Plate, V-Bottom, Square Well | 8.5 mL |
| Scienfocus 96 Well Culture Plate with Lid | 220 µL |

---

## Experiment and Software Setup

### Monomer Software Stack

Two main components:
1. **Monomer Culture Monitor** — Cloud data management platform for viewing experimental data in a plate-based format, built specifically for cell culture.
2. **Monomer Automation Platform** — Lab automation scheduler which coordinates the execution of experimental operations on scientific instruments.

### Running Experiments

Experiments are run using pre-developed **Routines** organized into **Workflows**, instantiated on the workcell via MCP.

#### Routines

**Measurement Routines** (two variants depending on plate type):
- Measure Cell Culture Stock Absorbance — for the 24-well Cell Culture Stock Plate
- Measure Experiment Plate Absorbance — for the 96-well Experiment Plate
- Both take `culture_plate_barcode` and `wells_to_process` as inputs

**Transfer Samples Routine** (Hackathon Transfer Samples):
Puts 3 plates on deck:

| Plate | Barcode Pattern | Labware | Notes |
|-------|----------------|---------|-------|
| Reagent Stock Plate | <TEAM_NAME>_REAGENTS | 24-well v-bottom deep well | 8.5 mL max per well; pre-filled with known reagent stocks |
| Experiment Plate | <TEAM_NAME>_EXPERIMENT | 96-well flat bottom | Empty at the start of each run |
| Cell Culture Stock Plate | <TEAM_NAME>_CELLS | 24-well flat bottom | ~2 mL per well of cell culture |

**Transfer Array Example:**
```python
transfer_array = [
    {
        "src_plate": "reagent",
        "src_well": "D1",
        "dst_plate": "experiment",
        "dst_well": "A1",
        "volume": 180,
        "new_tip": "once",
        "blow_out": True,
    },
    {
        "src_plate": "cell_culture_stock",
        "src_well": "A1",
        "dst_plate": "experiment",
        "dst_well": "A1",
        "volume": 20,
        "post_mix_volume": 40,
        "post_mix_reps": 5,
        "new_tip": "always",
        "blow_out": False,  # So as not to produce bubbles before measuring absorbance
    }
]
```

#### Workflow

A Workflow is a set of instructions in Python to execute a series of Routines at specific times with specific parameters.

**Example:** Measure Plate absorbance every 10 minutes for 2 hours, then passage 50 µLs of A1 into B1 filled with media = 12 × Measure Absorbance routines + 1 × Hackathon Transfer Samples routine.

### Part 1 — Workcell Tutorial

Use Cursor or Claude Code with the following prompt:

> Guide me through this tutorial: https://github.com/monomerbio/monomer-bio-hackathon-march14-15 step-by-step.

Steps:
1. **Setup:** Connect both teams to Monomer's MCPs
2. **Design:** Design a workflow to test seeding density impact on growth curves in standard media
3. **Execute:** Monomer Staff reviews the workflow, then loads it into the system. Workflow executes over ~1.5 hours
4. **Analyze:** Use Monomer's MCP to perform analysis on the different growth curves

### Part 2 — Autonomous Experimentation

Design → Execute → Analyze loops with Agents that analyze and propose next designs.

**Process:**
1. Design experiments using available reagent stocks (or mix your own component stocks)
2. Submit initial plate designs to Monomer (Reagent Stock Plate and Cell Culture Stock Plate)
3. Share a Google Doc with carter@monomerbio.com explaining reagent layout (use provided template)
4. Monomer can prepare up to 2 "Composed Media" (e.g., LBv2 or Minimal Defined Media) plus dilutions of existing stocks
5. Begin experimental cycles: Design workflow → Execute → Analyze → Design based on new data
6. First workflow needs approval; Monomer Staff will turn on auto-approve for subsequent workflows
7. Solutions can be added to the stock plate between iterations if precipitation occurs

### Wishlist / Goals

- **Autonomous experimentation:** Build something that continuously loops — closed-loop (gradient descent, Bayesian optimization) or agentic (scientific agent reviewing literature and exploring new hypotheses)
- **A (vibe coded) dashboard:** Showing experiment progress over time and whether the objective function minimizes at each iteration
- **A White Paper:** Describing the architecture and workflow
