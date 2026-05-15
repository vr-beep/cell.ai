# VSM — Media Optimization (One-Pager)

**Goal:** optimize media for V. natriegens (NaCl, Glucose, Yeast Extract with Tryptone=10 g/L).

---

## Scientific context

**Strain:** Novel Media Strain (Novel Biologics) — engineered V. natriegens, modified for plasmid over-production. Source: `Notion/Format-and-Tutorials/Vibrio-Natriegens-Materials-and-Resources.md:13`.

**Literature context:** LBv2 (10 g/L Tryptone, 5 g/L Yeast Extract, 25 g/L NaCl) is a widely accepted starting recipe, but the optimum concentrations (especially NaCl and sugar) depend on the strain, the experimental goal, and interact with other components. There is no consensus on the numbers — published NaCl optima differ by 2-3× between groups (15-25 g/L per Long et al. 2019 vs 7.5-15 g/L per Schleicher et al. 2024). The key parameter is probably not NaCl itself, but osmolality (optimum 1.0-1.6 Osmol/kg).

**Implication for the experiment:** we are not looking for the "correct" answer, we are **systematically mapping the response surface** via Bayesian optimization instead of the one-factor-at-a-time approach of earlier work.

**Sources:**
- Long et al. 2019, bioRxiv — https://www.biorxiv.org/content/10.1101/775437v1.full
- Schleicher et al. 2023, Appl Microbiol Biotechnol — https://link.springer.com/article/10.1007/s00253-023-12799-4
- Schleicher et al. 2024, BMC Biotechnology — https://bmcbiotechnol.biomedcentral.com/articles/10.1186/s12896-024-00897-8

---

## Project inventory

### 18 individual reagents (`reagents/reagents_set.csv`)

| # | Reagent | Stock |
|---|---|---|
| 1 | Tryptone (Vegetable) | 100 mg/mL |
| 2 | Yeast Extract | 100 mg/mL |
| 3 | Glycerol | 10% in sterile H2O |
| 4 | Glucose | 100 mg/mL |
| 5 | Sodium Chloride (NaCl) | 5 M |
| 6 | Magnesium Sulfate (MgSO4) | 1 M |
| 7 | Potassium Chloride (KCl) | 2 M |
| 8 | Ammonium Sulfate ((NH4)2SO4) | 1 M |
| 9 | Potassium Phosphate dibasic (K2HPO4) | 1 M |
| 10 | Potassium Phosphate monobasic (KH2PO4) | 1 M |
| 11 | MOPS (pH adjusted to 7) | 1 M |
| 12 | Calcium Chloride (CaCl2) | 1 M |
| 13 | Trace metals solution | 1000× |
| 14 | HCl | 12 N |
| 15 | NaOH | 10 N |
| 16 | Sodium Citrate | 1 M |
| 17 | Sodium L-Glutamate Monohydrate | 1 M |
| 18 | Iron(II) sulfate heptahydrate (FeSO4·7H2O) | 1 M |

### 6 base media (`reagents/base_media_set.csv` + Notion/Media-Recipes)

**1. Prepared LBv2** — classic LB with elevated salt

| Component | Final conc. |
|---|---|
| NaCl | 375 mM (~22 g/L) |
| Tryptone | 10 mg/mL |
| Yeast Extract | 5 mg/mL |
| KCl | 4 mM |
| MgSO4 | 2 mM |

**2. Novel Bio NBxCyclone** — optimized for plasmid production, pH 6.4, Tris buffer

| Component | Conc. |
|---|---|
| Yeast Extract | 15 g/L |
| Tryptone (vegetable) | 2.5 g/L |
| MgSO4 (anhydrous) | 4 g/L |
| NaCl | 22.5 g/L |
| K2HPO4 | 3 g/L |
| Tris buffer | 150 mM |
| **pH** | **6.4** |

**3. Defined-Minimal** — fully defined, NH4+ as N-source

| Component | Final conc. |
|---|---|
| NaCl | 275 mM (~16 g/L) |
| MOPS pH 7 | 40 mM |
| K2HPO4 | 4 mM |
| KH2PO4 | 1 mM |
| (NH4)2SO4 | 10 mM |
| Glucose | 2 mg/mL (0.2%) |
| Trace metals | 1× |
| MgSO4 | 1 mM |

**4. Semi-Defined** — Defined-Minimal + peptides

| Added to Defined-Minimal | Final conc. |
|---|---|
| Tryptone | 5 mg/mL |
| Yeast Extract | 2.5 mg/mL |

**5. High Buffer Defined** — Defined-Minimal with boosts for high-density

| Differences from Defined-Minimal | |
|---|---|
| MOPS | 100 mM (was 40 mM) |
| (NH4)2SO4 | 20 mM (was 10 mM) |
| Glucose | 4 mg/mL / 0.4% (was 0.2%) |

**6. Defined-Glycerol** — Defined-Minimal with glycerol instead of glucose (bypasses acetate overflow)

| Difference | |
|---|---|
| Glucose → Glycerol | 0.4% (w/v) |

### Inventory by biological axis

| Biological axis | Reagents from inventory |
|---|---|
| C-source | Glucose, Glycerol, Sodium Citrate, Sodium L-Glutamate |
| N-source | Tryptone, Yeast Extract, (NH4)2SO4, Sodium L-Glutamate |
| Osmolarity / salts | NaCl, KCl, (NH4)2SO4, Sodium Citrate |
| Cofactors / trace metals | MgSO4, CaCl2, FeSO4, Trace metals 1000× |
| pH buffering | MOPS, K2HPO4, KH2PO4, HCl, NaOH |
| Vitamins / growth factors | Only via Yeast Extract (no individual vitamins) |

**Precipitation constraints:** fully documented with numerical thresholds (PC1-PC17) in `Notion/Reagent-Compatibility-Guide.md`. Key ones:
- CaCl2 + any phosphate → immediate precipitate (PC2, PC3)
- MgSO4 + K2HPO4 > ~15 mM → precipitate; use KH2PO4 (PC4)
- MgSO4 + K2HPO4 + Sodium Citrate ≥ 12.5 mM → safe (PC5)
- KH2PO4 at pH 7 (MOPS) → ~40% → HPO4²⁻, precipitate with Ca²⁺/Mg²⁺ if divalent > 1-2 mM (PC13)
- CaSO4: if SO4²⁻ > 50 mM, Ca²⁺ < 1 mM (PC14)
- FeSO4 + K2HPO4 → incompatible, avoid (PC7)
- FeSO4 at pH 7 → Fe²⁺ → Fe³⁺, safe ≤ 10 µM with citrate, otherwise ~0 (PC16, PC17)

---

## Known operational constraints

Facts about the setup needed to interpret the VSM, but documented separately:
- Plate reader: OD600, path ~0.56 cm, kinetic every 10 min (`experimental-constraints.md:71-77`)
- Incubation: 30-37°C, optimal 37°C, Liconic STX-220 (`experimental-constraints.md:285`)
- Inoculum: LBv2 mid-log, OD ~0.05, 20 µL/well (`experimental-constraints.md:289-290, 11, 15`)
- Growth rate metric: μ_max, optimizer target = `mean_growth_rate_per_hr` (`scripts/baybe_opt.py:81, 280-288`)
- Plate layout: 60 usable wells, 3 reps + 1 blank, 11 conditions/plate (`experimental-constraints.md:50-52`)
- Incompatibility matrix: PC1-PC17 with numerical thresholds (`Notion/Reagent-Compatibility-Guide.md`)

Open gaps in the knowledge base (µL volumes, sterilization methods, strain biology, analysis pipeline code, baseline run) are tracked in `clarification-plan.md`.

---

## Current State VSM (manual workflow)

```
                                    ┌─────────────────────────────────┐
                                    │  PI: "optimize media"            │
                                    └──────────────┬──────────────────┘
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PROCESS BLOCKS (activity)                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  [A. DESIGN]        [B. PREP]         [C. EXECUTE]     [D. ANALYZE]  [E.DECIDE]│
│  Lit + DoE          Stocks +          Pipet + inoc     OD → growth   Next     │
│  + recipe calc      plate map         + incubate       rate          round    │
│  + plate map        + QC              + OD read        + viz         design   │
│                                                                                │
│  Scientist          Lab worker        Lab worker       Lab worker    Scientist│
│                                                        + Scientist   + PI     │
│                                                                                │
│  PT: 1.5 h          PT: 1.5 h         PT: 2 h          PT: 45 min    PT: 1 h  │
│  LT: 4 h            LT: 14 h          LT: 4 h          LT: 1.5 h     LT: 4 h  │
│                     (autoclave wait)  (incubation)                   (PI wait) │
│                                                                                │
│  %C&A: 80%          %C&A: 90%         %C&A: 70% ⚠     %C&A: 85%     %C&A: 70%│
└──────┬──────────────┬──────────────┬───────────────┬─────────────┬───────────┘
       │              │              │               │             │
       │ handoff      │ handoff      │ handoff       │ handoff     │ back to A
       ▼              ▼              ▼               ▼             │
     design         plate         raw CSV          plot +          │
     doc            ready         + blanks         interp   ───────┘
```

**Totals per round:**
- ΣPT = **~6.75 h** of active work
- ΣLT = **~27.5 h** calendar time
- Flow efficiency = **25%**
- Rolled %C&A across 4 handoffs: 0.8×0.9×0.7×0.85×0.7 ≈ **30%**
- → ~1 in 3 rounds requires rework somewhere in the chain

---

## Boxes detail

| Block | Inputs | Outputs | Tools | Waste |
|---|---|---|---|---|
| **A. Design** | PI brief, prev round data, literature | DoE table, recipe sheet (g/L + µL), plate map | PubMed, Excel template, Benchling | Motion (tab-switching), over-processing (manual Bayes guess) |
| **B. Prep** | Recipe sheet, stock inventory | Verified stocks, labeled tubes, clean plate | Autoclave, pH meter, scale | Waiting (autoclave), inventory (excess stocks) |
| **C. Execute** | Plate map, stocks, overnight culture | Plate with 60 wells inoculated, OD600 CSV | Multichannel pipette, shaker, plate reader | Rework (pipet errors), defects (contamination, edge effect), waiting (incubation — irreducible) |
| **D. Analyze** | Raw CSV | Growth rates per condition, plot | Python/Excel, blank-subtract script | Over-processing (if manual), transport (CSV→Excel→plot) |
| **E. Decide** | Plot + table | Next-round design brief | Meeting w/ PI | Waiting (PI availability), defects (cherry-pick winners, local optima) |

---

## Handoffs — where %C&A is lost

```
  Scientist ─────► Lab worker       A→B: recipe ambiguity, unit confusion (g/L vs µL)
  Lab worker ─────► Lab worker      B→C: plate map misread, tube mislabel
  Lab worker ─────► Scientist       C→D: blank wells unclear, edge wells not flagged
  Scientist ─────► PI               D→E: plot shows correlation, PI asks "why"
```

**Empirical rework drivers:**
1. Unit conversion in recipe calc — recurring, ~20% of rounds
2. Blank subtraction method inconsistent round-to-round — ~30% of rounds
3. Next-round design subjective — PI revisits decision ~40% of rounds

---

## Bottleneck analysis

| Constraint | Type | Mitigable? |
|---|---|---|
| **Incubation 2-4 h** | Physical (biology) | ❌ Irreducible — V. natriegens doubling is fixed |
| **PI availability for E** | Organizational | ⚠ Partial — async review possible |
| **Manual pipetting 1.5 h** | Human | ✅ Robot eliminates |
| **Recipe calc ambiguity** | Process | ✅ Deterministic compiler eliminates |
| **Autoclave 12 h LT** | Batch equipment | ⚠ Partial — batch prep once for all rounds |

**Theory of Constraints takeaway:** incubation is the true bottleneck. Everything done **during** incubation (analyze prev round, design next) is free capacity. Everything done **before/after** incubation is a target candidate for automation.

---

## Future State VSM (Cell.ai agent, honest estimate)

```
  [A'. DESIGN]       [B. PREP]       [C'. EXECUTE]    [D'. ANALYZE]   [E'. DECIDE]
  BayBE + Elnora     Stocks (same)   Robot pipet +    Arne parser +   BayBE next
  context +          (one-time       inoc + OD         blank subtract  + human
  compiler           batch prep)                       (deterministic) review

  Agent + PM         Lab worker      Lab worker +     Agent            Agent + PI
                                     robot                              (review only)

  PT: 15 min         PT: 1 h         PT: 45 min       PT: 5 min        PT: 15 min
  LT: 15 min         LT: 14 h (1×)   LT: 3.5 h        LT: 5 min        LT: 30 min
                     amortized       (incubation
                     across rounds   dominates)

  %C&A: 85%          %C&A: 90%       %C&A: 85%        %C&A: 95%        %C&A: 80%
```

**Per round (rounds 2+, after initial batch prep amortized):**
- ΣPT ≈ **2.25 h** (vs 6.75 h) — **3× reduction**
- ΣLT ≈ **4 h** (vs 27.5 h) — **7× reduction** (mostly from removing handoff waits)
- Rolled %C&A ≈ **55%** (vs 30%) — **~2× reduction in rework rate**

---

## Future State — Boxes detail

| Block | Inputs | Outputs | Tools | What changed vs Current |
|---|---|---|---|---|
| **A'. Design** | PI goal, prev round CSV, Elnora lit context | BayBE-generated DoE table, compiled µL recipe, plate map JSON | BayBE optimizer, Elnora MCP (literature), deterministic g/L→µL compiler | Unit conversion — zero-error. Next-round design — algorithmic, not intuition. Lit context — auto-injected, not manual reading. |
| **B. Prep** | Compiled recipe, stock inventory | Verified stocks, labeled tubes, clean plate | Autoclave, pH meter, scale | **Unchanged** — physical step. Mitigation: batch prep once, amortize LT. |
| **C'. Execute** | Plate map JSON, stocks, overnight culture | Inoculated plate, OD600 CSV | Monomer MCP (robot pipette), shaker, plate reader | Pipetting errors ↓ (deterministic robot). Plate map misread eliminated (machine-readable). Incubation/OD read — unchanged. |
| **D'. Analyze** | Raw CSV | Growth rates, blank-corrected, viz | Arne parser (Python), BayBE ingest | Blank subtraction — deterministic and consistent round-to-round. CSV→Excel→plot transport removed. Auto-flags edge wells and artifacts. |
| **E'. Decide** | Growth rates + BayBE posterior | Next-round DoE + uncertainty | BayBE acquisition function + PI review (async) | Cherry-picking eliminated. PI review is a sanity check, not design. Async — removes "waiting for PI" waste. |

**Handoffs in future state:**

```
  Agent ─────► Lab worker       A'→B: machine-readable recipe, no ambiguity
  Lab worker ─────► Robot       B→C': plate map JSON loaded directly
  Robot ─────► Agent            C'→D': CSV auto-ingested
  Agent ─────► PI               D'→E': PI reviews plot + BayBE recommendation
```

Handoff count is the same (4), but 3 of 4 are machine-to-machine, with %C&A close to 100% on those transitions. The only human handoff is E' (PI review), which is kept deliberately for safety.

---

## Analytical conclusions

1. **Incubation (2-4 h) is an irreducible bottleneck.** V. natriegens biology is fixed; this is not a target for process optimization.
2. **The biggest PT savings are in steps A and D**, not C. The pipetting robot closes pipetting errors, but compiler + parser + optimizer save more PT per round.
3. **Batch stock prep** is an amortized cost across many rounds; it moves from critical path to pre-run.
4. **E (decide) is the point where human oversight is most valuable.** The agent accelerates the decision but shrinks the surface for human review. The trade-off between speed and safety is localized in this block.
