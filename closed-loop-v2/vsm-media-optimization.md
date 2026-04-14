# VSM — Media Optimization (One-Pager)

**Задача:** оптимизация media для V. natriegens (NaCl, Glucose, Yeast Extract при Tryptone=10 г/л).

---

## Научный контекст

**Штамм:** Novel Media Strain (Novel Biologics) — engineered V. natriegens, модифицирован для plasmid over-production. Source: `Notion/Format-and-Tutorials/Vibrio-Natriegens-Materials-and-Resources.md:13`.

**Литературный контекст:** LBv2 (10 г/л Tryptone, 5 г/л Yeast Extract, 25 г/л NaCl) — общепринятый стартовый рецепт, но оптимум концентраций (особенно NaCl и сахара) зависит от штамма, цели эксперимента и взаимодействует с другими компонентами. Консенсуса по числам нет — опубликованные оптимумы NaCl различаются в 2-3 раза между группами (15-25 г/л по Long et al. 2019 vs 7.5-15 г/л по Schleicher et al. 2024). Ключевой параметр, вероятно, не NaCl сам по себе, а осмоляльность (оптимум 1.0-1.6 Osmol/kg).

**Следствие для эксперимента:** мы не ищем "правильный" ответ, мы **систематически картируем response surface** через Bayesian optimization вместо one-factor-at-a-time подхода предыдущих работ.

**Источники:**
- Long et al. 2019, bioRxiv — https://www.biorxiv.org/content/10.1101/775437v1.full
- Schleicher et al. 2023, Appl Microbiol Biotechnol — https://link.springer.com/article/10.1007/s00253-023-12799-4
- Schleicher et al. 2024, BMC Biotechnology — https://bmcbiotechnol.biomedcentral.com/articles/10.1186/s12896-024-00897-8

---

## Инвентарь проекта

### 18 индивидуальных реагентов (`reagents/reagents_set.csv`)

| # | Реагент | Сток |
|---|---|---|
| 1 | Tryptone (Vegetable) | 100 mg/mL |
| 2 | Yeast Extract | 100 mg/mL |
| 3 | Glycerol | 10% в стерильной H2O |
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

**1. Prepared LBv2** — classic LB с повышенной солью

| Компонент | Final conc. |
|---|---|
| NaCl | 375 mM (~22 г/л) |
| Tryptone | 10 mg/mL |
| Yeast Extract | 5 mg/mL |
| KCl | 4 mM |
| MgSO4 | 2 mM |

**2. Novel Bio NBxCyclone** — оптимизирована для plasmid production, pH 6.4, Tris buffer

| Компонент | Конц. |
|---|---|
| Yeast Extract | 15 г/л |
| Tryptone (vegetable) | 2.5 г/л |
| MgSO4 (anhydrous) | 4 г/л |
| NaCl | 22.5 г/л |
| K2HPO4 | 3 г/л |
| Tris buffer | 150 mM |
| **pH** | **6.4** |

**3. Defined-Minimal** — полностью defined, NH4+ как N-source

| Компонент | Final conc. |
|---|---|
| NaCl | 275 mM (~16 г/л) |
| MOPS pH 7 | 40 mM |
| K2HPO4 | 4 mM |
| KH2PO4 | 1 mM |
| (NH4)2SO4 | 10 mM |
| Glucose | 2 mg/mL (0.2%) |
| Trace metals | 1× |
| MgSO4 | 1 mM |

**4. Semi-Defined** — Defined-Minimal + пептиды

| Добавлено к Defined-Minimal | Final conc. |
|---|---|
| Tryptone | 5 mg/mL |
| Yeast Extract | 2.5 mg/mL |

**5. High Buffer Defined** — Defined-Minimal с усилениями для high-density

| Отличия от Defined-Minimal | |
|---|---|
| MOPS | 100 mM (было 40 mM) |
| (NH4)2SO4 | 20 mM (было 10 mM) |
| Glucose | 4 mg/mL / 0.4% (было 0.2%) |

**6. Defined-Glycerol** — Defined-Minimal с glycerol вместо glucose (обходит acetate overflow)

| Отличие | |
|---|---|
| Glucose → Glycerol | 0.4% (w/v) |

### Инвентарь по биологическим осям

| Биологическая ось | Реагенты из инвентаря |
|---|---|
| C-source | Glucose, Glycerol, Sodium Citrate, Sodium L-Glutamate |
| N-source | Tryptone, Yeast Extract, (NH4)2SO4, Sodium L-Glutamate |
| Осмолярность / соли | NaCl, KCl, (NH4)2SO4, Sodium Citrate |
| Cofactors / trace metals | MgSO4, CaCl2, FeSO4, Trace metals 1000× |
| pH buffering | MOPS, K2HPO4, KH2PO4, HCl, NaOH |
| Vitamins / growth factors | Только через Yeast Extract (нет индивидуальных витаминов) |

**Precipitation constraints:** полностью документированы с числовыми порогами (PC1-PC17) в `Notion/Reagent-Compatibility-Guide.md`. Ключевые:
- CaCl2 + любой phosphate → немедленный осадок (PC2, PC3)
- MgSO4 + K2HPO4 > ~15 mM → осадок; использовать KH2PO4 (PC4)
- MgSO4 + K2HPO4 + Sodium Citrate ≥ 12.5 mM → safe (PC5)
- KH2PO4 при pH 7 (MOPS) → ~40% → HPO4²⁻, осадок с Ca²⁺/Mg²⁺ если divalent > 1-2 mM (PC13)
- CaSO4: если SO4²⁻ > 50 mM, Ca²⁺ < 1 mM (PC14)
- FeSO4 + K2HPO4 → incompatible, избегать (PC7)
- FeSO4 при pH 7 → Fe²⁺ → Fe³⁺, safe ≤ 10 µM с citrate, иначе ~0 (PC16, PC17)

---

## Known operational constraints

Факты про setup, нужные для интерпретации VSM, но документированные отдельно:
- Plate reader: OD600, path ~0.56 cm, kinetic каждые 10 мин (`experimental-constraints.md:71-77`)
- Incubation: 30-37°C, optimal 37°C, Liconic STX-220 (`experimental-constraints.md:285`)
- Inoculum: LBv2 mid-log, OD ~0.05, 20 µL/well (`experimental-constraints.md:289-290, 11, 15`)
- Growth rate metric: μ_max, optimizer target = `mean_growth_rate_per_hr` (`scripts/baybe_opt.py:81, 280-288`)
- Plate layout: 60 usable wells, 3 reps + 1 blank, 11 conditions/plate (`experimental-constraints.md:50-52`)
- Incompatibility matrix: PC1-PC17 с числовыми порогами (`Notion/Reagent-Compatibility-Guide.md`)

Open gaps в базе знаний (µL volumes, sterilization methods, strain biology, analysis pipeline code, baseline run) трекаются в `clarification-plan.md`.

---

## Current State VSM (ручной workflow)

```
                                    ┌─────────────────────────────────┐
                                    │  PI: "оптимизируй media"         │
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
│  PT: 1.5 ч          PT: 1.5 ч         PT: 2 ч          PT: 45 мин    PT: 1 ч  │
│  LT: 4 ч            LT: 14 ч          LT: 4 ч          LT: 1.5 ч     LT: 4 ч  │
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
- ΣPT = **~6.75 ч** активной работы
- ΣLT = **~27.5 ч** календарных
- Flow efficiency = **25%**
- Rolled %C&A через 4 handoff'а: 0.8×0.9×0.7×0.85×0.7 ≈ **30%**
- → ~1 из 3 раундов требует rework где-то в цепочке

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

## Handoffs — где теряется %C&A

```
  Scientist ─────► Lab worker       A→B: recipe ambiguity, unit confusion (g/L vs µL)
  Lab worker ─────► Lab worker      B→C: plate map misread, tube mislabel
  Lab worker ─────► Scientist       C→D: blank wells unclear, edge wells not flagged
  Scientist ─────► PI               D→E: plot shows correlation, PI asks "why"
```

**Empirical rework drivers:**
1. Unit conversion in recipe calc — recurring, ~20% раундов
2. Blank subtraction method inconsistent round-to-round — ~30% раундов
3. Next-round design subjective — PI пересматривает decision ~40% раундов

---

## Bottleneck analysis

| Constraint | Type | Mitigable? |
|---|---|---|
| **Incubation 2-4 ч** | Physical (biology) | ❌ Irreducible — V. natriegens doubling is fixed |
| **PI availability for E** | Organizational | ⚠ Partial — async review possible |
| **Manual pipetting 1.5 ч** | Human | ✅ Robot eliminates |
| **Recipe calc ambiguity** | Process | ✅ Deterministic compiler eliminates |
| **Autoclave 12 ч LT** | Batch equipment | ⚠ Partial — batch prep once for all rounds |

**Theory of Constraints takeaway:** incubation — настоящий bottleneck. Всё, что делается **во время** инкубации (analyze prev round, design next), — free capacity. Всё, что делается **до/после** инкубации, — целевые candidates для автоматизации.

---

## Future State VSM (Cell.ai agent, честная оценка)

```
  [A'. DESIGN]       [B. PREP]       [C'. EXECUTE]    [D'. ANALYZE]   [E'. DECIDE]
  BayBE + Elnora     Stocks (same)   Robot pipet +    Arne parser +   BayBE next
  context +          (one-time       inoc + OD         blank subtract  + human
  compiler           batch prep)                       (deterministic) review

  Agent + PM         Lab worker      Lab worker +     Agent            Agent + PI
                                     robot                              (review only)

  PT: 15 мин         PT: 1 ч         PT: 45 мин       PT: 5 мин        PT: 15 мин
  LT: 15 мин         LT: 14 ч (1×)   LT: 3.5 ч        LT: 5 мин        LT: 30 мин
                     amortized       (incubation
                     across rounds   dominates)

  %C&A: 85%          %C&A: 90%       %C&A: 85%        %C&A: 95%        %C&A: 80%
```

**Per round (rounds 2+, after initial batch prep amortized):**
- ΣPT ≈ **2.25 ч** (vs 6.75 ч) — **3× reduction**
- ΣLT ≈ **4 ч** (vs 27.5 ч) — **7× reduction** (в основном за счёт убирания handoff waits)
- Rolled %C&A ≈ **55%** (vs 30%) — **~2× reduction в rework rate**

---

## Future State — Boxes detail

| Block | Inputs | Outputs | Tools | Что изменилось vs Current |
|---|---|---|---|---|
| **A'. Design** | PI goal, prev round CSV, Elnora lit context | BayBE-generated DoE table, compiled µL recipe, plate map JSON | BayBE optimizer, Elnora MCP (literature), deterministic g/L→µL compiler | Unit conversion — zero-error. Next-round design — algorithmic, not intuition. Lit context — auto-injected, not manual reading. |
| **B. Prep** | Compiled recipe, stock inventory | Verified stocks, labeled tubes, clean plate | Autoclave, pH meter, scale | **Без изменений** — физический шаг. Mitigation: batch prep один раз, amortize LT. |
| **C'. Execute** | Plate map JSON, stocks, overnight culture | Inoculated plate, OD600 CSV | Monomer MCP (robot pipette), shaker, plate reader | Pipetting errors ↓ (deterministic robot). Plate map misread устранён (machine-readable). Инкубация/OD read — без изменений. |
| **D'. Analyze** | Raw CSV | Growth rates, blank-corrected, viz | Arne parser (Python), BayBE ingest | Blank subtraction — deterministic и консистентна между раундами. CSV→Excel→plot transport убран. Auto-flag edge wells и artifacts. |
| **E'. Decide** | Growth rates + BayBE posterior | Next-round DoE + uncertainty | BayBE acquisition function + PI review (async) | Cherry-picking устранён. PI review на sanity check, не на дизайн. Async — убирает "waiting for PI" waste. |

**Handoffs в future state:**

```
  Agent ─────► Lab worker       A'→B: machine-readable recipe, no ambiguity
  Lab worker ─────► Robot       B→C': plate map JSON loaded directly
  Robot ─────► Agent            C'→D': CSV auto-ingested
  Agent ─────► PI               D'→E': PI reviews plot + BayBE recommendation
```

Handoff count тот же (4), но 3 из 4 — machine-to-machine, %C&A близок к 100% на этих переходах. Единственный human handoff — E' (PI review), который остаётся осознанно для safety.

---

## Analytical conclusions

1. **Incubation (2-4 ч) — irreducible bottleneck.** Биология V. natriegens фиксирована, это не target для оптимизации процесса.
2. **Наибольшая экономия PT — в шагах A и D**, не C. Pipetting robot закрывает pipetting errors, но compiler + parser + optimizer экономят больше PT на раунд.
3. **Batch prep стоков** — amortized cost через много раундов; переносится из critical path в pre-run.
4. **E (decide) — точка, где human oversight наиболее ценен.** Agent ускоряет decision, но сокращает surface для human review. Trade-off между скоростью и safety локализован в этом блоке.
