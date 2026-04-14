# Plan: Clarification of Media Optimization Knowledge Base

## Context

Готовим новый эксперимент по media optimization для V. natriegens (Novel Media Strain) под paper. Часть knowledge base уже документирована (plate reader, incubation, inoculum, plate layout, incompatibility matrix PC1-PC17) в `experimental-constraints.md`, `Notion/Media-Recipes/` и `Notion/Reagent-Compatibility-Guide.md`. Этот план закрывает оставшиеся пробелы.

**SoT audit (2026-04-14)** выявил критичный P0 bug: BayBE search space включает реагенты, физически отсутствующие на reagent plate. Запуск без fix'а → artifact data.

Цель: к моменту старта иметь (а) canonical sources зафиксированы и stale игнорируются, (б) BayBE search space только по реагентам на plate, (в) ответы Monomer по prep protocol и data pipeline, (г) baseline growth на всех 6 base media.

---

## Source-of-truth (verified 2026-04-14)

| Параметр | Canonical source | Stale — НЕ использовать |
|---|---|---|
| Reagent plate layout (A1-D4) | `POC/closed-loop/scripts/tools/compiler.py:16-42` (verified Arne MCP) | — |
| Активные реагенты (11 на plate) | `compiler.py STOCKS` | `doc/hackathon/reagents.md` (16, устарело) |
| Placeholder реагенты (НЕ на plate) | `compiler.py` comments: Tryptone, Na L-Glut, KH2PO4 → C3 placeholder | Любые refs к ним как knobs |
| Base media recipes | `doc/hackathon/experimental-constraints.md:316-476` | — |
| Strain | `Notion/Format-and-Tutorials/Vibrio-Natriegens-Materials-and-Resources.md:13` = Novel Media Strain | — |
| Workcell hardware | `Notion/Format-and-Tutorials/Track-A-Materials/Monomer-Workcell.md:9-17` | — |
| Round data | `/data/data_by_round/` (корневой) | `POC/closed-loop/data/data_by_round/` (duplicate) |
| BayBE config | `scripts/baybe_opt.py` | — |

### Workcell hardware (canonical)
- Liquid handler: **Opentrons Flex**
- Plate reader: **Tecan Infinite**
- Incubator 37°C: **Liconic STX-220**
- Carousel: **Liconic LPX-220**
- Cold storage 4°C: **Liconic STX-110**
- Robotic arm: **KX-2**
- Max transfers per protocol: 50 (docs say 40)
- Final well volume: 200 µL (180 µL reagent + 20 µL cells default)
- Min pipettable: ~5-10 µL

---

## Редуцированный список gaps

### Group 0 — Code bug + pre-plate-1 blockers (P0)
**G0.1** **BayBE placeholder bug** — `scripts/baybe_opt.py:42-79` оптимизирует по Tryptone, Na L-Glut, KH2PO4, которых нет на plate (все указывают на well C3 как placeholder в `compiler.py`). Если запустить — BayBE предложит рецепты с этими реагентами, robot pipetting из пустой C3 → дикий artifact. **Блокирует любой новый run.** Fix: ограничить search space в `baybe_opt.py` только реальными реагентами из `compiler.py STOCKS` (yeast_extract, mops, glucose, nacl, mgso4, nh4so4, trace_metals, glycerol). Add MOPS as optimization knob (100-300 mM) per Elnora revision.

**G0.2 (NEW)** **Cultivarium DoE condition 14 retrieval** — paper bioRxiv 2026.02.11.705132v1 supplementary text 8 содержит их optimal concentrations из RSM optimization. Читать PDF `/Users/viachealavrudenko/Downloads/2026.02.11.705132v1.full.pdf` supplementary, extract YE/tryptone/MgSO4/NaCl/K2HPO4 concentrations для использования как **warm-start seed point** в BayBE initial LHS для Plate 1. Methodologically sound per Elnora [verified]. ~1 hour.

**G0.3** **Tecan Infinite API format** — plate reader отдаёт raw kinetic OD per timepoint или pre-processed growth_rate? Ответ определяет scope `analyzer.py` fix'а. Email Monomer.

**G0.4 (NEW)** **Strain antibiotic marker** — Novel Media Strain создан для plasmid overproduction, но antibiotic / selectable marker не задокументирован. Нужен для (a) post-plate 4 replica spotting для plasmid retention verification, (b) methods section paper'а. Email Novel Biologics или Monomer. Без этого ответа — plasmid retention check невозможен → caveat в paper.

### Group 1 — Monomer prep protocol (вопросы к Monomer)
Workflow — Pattern A (bulk prep): Monomer staff готовит bulk base media в reagent plate wells A1-B2, робот (Opentrons Flex) берёт оттуда 110-180 µL на condition + добавляет supplements + water + cells. Подтверждено в `POC/closed-loop/scripts/tools/compiler.py:32-39, 88-93` и `experimental-constraints.md:311`. G1.1 (µL volumes per recipe) — не gap, compiler уже существует, нужна только валидация.

**G1.2** Sterilization method для 5 из 6 base media (только NBxCyclone документирован — 0.2 µm filter). Нужно для paper methods section.
**G1.3** Prep timing / shelf life — за сколько до run готовятся bulk media, как долго хранятся при 4°C.
**G1.4** Volume prep per reagent well — 24-well deep well max 8.5 mL, фактический fill-level неизвестен.
**G1.5 (NEW)** Готов ли Monomer физически добавить Tryptone / Na L-Glut / KH2PO4 как стоки на reagent plate? Если да — можем вернуть их в BayBE search space; если нет — permanent removal.

### Group 2 — Physical conditions
**G2.1** Shaking speed (rpm) во время incubation.
**G2.2** Humidity control в incubator (для evaporation / edge effect).

### Group 3 — Analysis pipeline
**G3.1** Ответ Monomer: plate reader API отдаёт raw kinetic OD или pre-processed growth rates? От этого зависит, нужен ли нам код для `fit_exponential(time, od)` или нет.
**G3.2** Blank subtraction — простая версия (вычитать mean blank per timepoint) достаточна; magnitude artifact'ов от glucose/NaCl надо эмпирически проверить на baseline run.
**G3.3** Verification: проверить, что существующие plate map CSV не назначают conditions в edge wells (A/H rows, 1/12 columns). Если plate map уже avoid edge — G3.4 не нужен.
**G3.4** ~~Outlier detection~~ — отложено. Статистика на n=3 ненадёжна, проще визуально проверять по первым раундам.

### Group 4 — Strain biology (for paper)
**G4.1** Plasmid identity и selectable marker для Novel Media Strain.
**G4.2** Antibiotic supplementation requirements.
**G4.3** Genotype modifications относительно wild-type V. natriegens.

### Group 5 — Baseline calibration (experimental)
**G5.1** Doubling time / μ_max / max OD на каждой из 6 base media без оптимизации. Требует 1 plate × 3 replicates × 6 conditions ≈ 18 wells + blanks.

### Group 6 — Reagent handling (lower priority)
**G6.1** Stock stability / storage temp / prep dates из SDS (URLs есть в `reagents/reagents_set.csv`).
**G6.2** Maillard handling в prep protocol (glucose отдельно от пептидов при автоклаве).

---

## Approach

**Три параллельных трека, каждый со своим owner и deliverable.**

### Track A — Monomer email (async, external)
Consolidated запрос к Monomer, одно сообщение закрывает большинство gaps:

1. **Prep protocol (G1.2-G1.4):** для каждой из 5 base media (LBv2, Defined-Minimal, Semi-Defined, High Buffer Defined, Defined-Glycerol) — какой sterilization method (autoclave/filter), timing before robot run, shelf life при 4°C, volume fill per reagent well.
2. **Plate extension (G1.5):** готовы ли физически добавить Tryptone / Na L-Glut / KH2PO4 как реальные стоки на reagent plate? Если да — в какие wells?
3. **Incubator conditions (G2.1-G2.2):** shaking rpm и humidity control в Liconic STX-220.
4. **Data pipeline (G0.3):** Tecan Infinite API отдаёт raw kinetic OD или pre-processed growth rates? Если raw — какой формат CSV.
5. **Volume/shaking validation:** подтверждение что 150 µL total в 96-well работоспособно (меньше standard 200 µL но улучшает OTR).
6. **Pre-warming protocol:** есть ли option pre-warm reagent plate до 37°C перед robot run (избегает μ_max depression первые 30-60 мин).
7. **Strain (G4.1-G4.3, G0.4):** для Novel Media Strain — plasmid identity, **selectable marker / antibiotic** (critical для plasmid retention), genotype relative to ATCC 14048. **Если Monomer не знает — redirect к Novel Biologics (matthew.weinstock@novel-bio.com per Cultivarium paper).**

Deliverable: ответы Monomer запротоколированы в `experimental-constraints.md`.

### Track B — Code fix + analysis (Slava + Arne)
**P0 priority — G0.1 BayBE search space fix:**
1. Edit `scripts/baybe_opt.py:42-79`:
   - Удалить (или `disabled=True`) параметры tryptone, na_l_glut, kh2po4
   - Оставить: yeast_extract, mops, glucose, nacl, mgso4, nh4so4, trace_metals, glycerol
   - **Expand bounds per Elnora revision:** NaCl 10-30 g/L, Glucose 5-20 g/L, YE 0-10 g/L (added), MOPS 100-300 mM
   - Add MOPS as optimization knob (was not in search space)
2. Verification: BayBE dry-run → все proposed conditions используют только реагенты из `compiler.py STOCKS`; все values в bounds.

**P0 — G0.2 Cultivarium seed retrieval:**
3. Read `/Users/viachealavrudenko/Downloads/2026.02.11.705132v1.full.pdf` supplementary text 8. Extract "condition 14" YE/Tryptone/MgSO4/NaCl/K2HPO4 concentrations. Add to BayBE initial LHS as 1 warm-start seed.

**Consistency cleanup:**
4. Пометить `doc/hackathon/reagents.md` как OUTDATED (header) — conflicts с `compiler.py STOCKS`.

**Analysis pipeline (conditional на G0.3 ответ):**
- Если Monomer отдаёт raw kinetic: добавить `fit_exponential(time, od)` + blank-subtraction в `analyzer.py` (~5-10 строк каждое). Plus physical sanity filter: flag μ > 4.5 h⁻¹ as artifact.
- Если pre-processed: add sanity filter only.

**Edge wells verification:** grep existing plate map CSV на edge wells в condition assignments. Если ни один condition не в A/H rows или columns 1/12 — edge filter не нужен.

Reuse: existing `compiler.py`, `analyzer.py`.

### Track C — Plate 1 (Deep BO on Semi-Defined)
Цель: запустить revised Plate 1 per `experimental-campaign.md`.

**Revised strategy** (после Elnora critique): не broad screen 4 media × 4 conditions (mathematically underpowered), а **1 media × 17 LHS × 3 reps**.

Steps:
1. **Plate 1 run** after A + B dependencies resolved: 17 LHS conditions на Semi-Defined + 3 NBxCyclone anchor + 3 LBv2 anchor + 3 blanks = 60 usable wells.
   - Volume: 150 µL total (135 media + 15 cells)
   - Inoculum: OD 0.01 (not historical 0.05)
   - Kinetic OD600 каждые 10 мин × 4 часа
   - Pre-warm reagent plate to 37°C before run
2. If G0.2 resolved: 1 of 17 LHS points = Cultivarium condition 14 (warm-start).
3. If G0.4 resolved: post-run replica spot top wells onto ±antibiotic agar для plasmid retention baseline.

Requires: A (Monomer responses for G1.2-G1.5, G0.3, G0.4), B (G0.1 fix, G0.2 seed, G0.3 conditional analyzer).

Deliverable: `SOT/experiments/plate1_growth.csv` + `plate1_plate_condition_map.csv`. GP posterior documented в `experimental-campaign.md` per-plate log.

### Deferred
- **G3.4** (code outlier detection) — отложено до empirical evidence от baseline run.
- **G6.1** (stock stability) и **G6.2** (Maillard handling) — P2, opportunistically при следующем касании SDS.

---

## Critical files

**Reused (canonical read-only):**
- `POC/closed-loop/scripts/tools/compiler.py` (lines 16-42) — reagent plate layout canonical
- `doc/hackathon/experimental-constraints.md` (316-476) — base media recipes + plate reader + inoculum
- `Notion/Reagent-Compatibility-Guide.md` — PC1-PC17 numeric thresholds
- `Notion/Format-and-Tutorials/Track-A-Materials/Monomer-Workcell.md` — workcell specs
- `Notion/Media-Recipes/*.md` — secondary reference (consistent with experimental-constraints.md)
- `reagents/reagents_set.csv` — SDS URLs + stock concentrations (18 listed)
- `reagents/base_media_set.csv` — список 6 base media
- `POC/closed-loop/scripts/tools/analyzer.py` — existing analysis stub
- `scripts/baybe_opt.py` — BayBE config (has G0.1 bug to fix)
- `/data/data_by_round/` (root, не POC/) — historical rounds

**Modified:**
- `scripts/baybe_opt.py` (G0.1 P0 fix — remove placeholder reagents)
- `POC/closed-loop/scripts/tools/analyzer.py` (conditional G3)
- `doc/hackathon/experimental-constraints.md` (Track A responses, strain detail)
- `doc/hackathon/reagents.md` (mark OUTDATED или удалить)

**New:**
- `SOT/experiments/plate1_growth.csv` + `plate1_plate_condition_map.csv` (Track C after Plate 1)
- `closed-loop-v2/experimental-campaign.md` — living doc для plate-by-plate decisions (created)

**Stale — НЕ использовать:**
- `doc/hackathon/reagents.md` (outdated 16-reagent list, conflicts с compiler.py STOCKS)
- `POC/closed-loop/data/data_by_round/` (duplicate of root `/data/`)

---

## Sequencing

**Can run in parallel:**
- Track A и Track B — независимые, чистый код/docs.
- Track C pt. 2-3 (emails) — асинхронно, ждём ответов.

**Sequential dependency:**
- Track C pt. 1 (baseline run) требует Track A compiler готовым (чтобы pipetting был корректным), и Track B analyzer готовым (чтобы обработать baseline raw OD).
- После baseline run — GO/NO-GO для optimization round.

Order of operations:
1. Tracks A + B параллельно; Track C emails отправлены асинхронно.
2. Track A/B review + fix после ответов от Monomer/Novel Biologics.
3. Baseline run (Track C pt. 1) с готовым pipeline.
4. Анализ baseline, GO/NO-GO.
5. Следующий round optimization.

---

## Verification

**G0.1 BayBE fix (P0):**
- `grep -E "tryptone|na_l_glut|kh2po4" scripts/baybe_opt.py` → не возвращает active search params (только comments/disabled).
- BayBE dry-run: 16 proposed conditions, все реагенты ∈ `compiler.py STOCKS` active keys.
- Compile первый condition через `compiler.py` — все src_wells ≠ C3 (placeholder well).

**Track A (Monomer responses):**
- Ответы протоколированы в `experimental-constraints.md` (секция "Monomer SoT responses"), все P0 вопросы закрыты.

**Track B (analysis):**
- Если добавили fit_exponential: unit test на synthetic curve `OD(t) = OD0 * exp(μ*t)` → recovery μ в пределах 5%.
- Если добавили blank-subtraction: blank OD = 0.03 постоянно, post-subtraction остаётся чистый growth signal.
- Edge-wells verification: grep plate map CSV на A/H rows и 1/12 cols — условия отсутствуют в edge.

**Track C (baseline):**
- CSV имеет 6 rows (по одной base media), μ_max, max_OD, lag_time.
- NBxCyclone anchor μ в диапазоне 2-4 h⁻¹ (sanity check против physical limit 4.43).
- fit_r2 > 0.98 для всех.
- Strain section в `experimental-constraints.md` содержит ≥1 факт помимо имени.

**Integration verification:**
- Полный round: fixed baybe_opt → compiler → robot → Tecan → analyzer → next recipe. No placeholder wells touched, no artifact OD values (μ > 4.43).
- Target: ΣLT ≤ 4 ч per round после baseline calibration.

---

## Open decisions

1. **Incompatibility matrix в BayBE constraints** — правила PC1-PC17 задокументированы, но не закодированы в BayBE search space. Предложение: добавить как Track B pt. 5.
2. **Кто owns Track C baseline run** — Nikki (bio expert) или lab worker по протоколу от Slava/Arne? Предложение: Nikki design, lab worker execute.
