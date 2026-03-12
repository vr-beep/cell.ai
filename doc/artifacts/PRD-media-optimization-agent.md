# PRD: AI-Driven Cell Culture Media Optimization Agent

**Project:** 24hr AI Science Cell Culture Hack @ Monomer Bio — Track A
**Date:** March 14-15, 2026
**Author:** Cell.ai team
**Status:** Reviewed — Mar 12, 2026

**Framing:** Every decision in this PRD is made through the lens of "does this help us win?" The narrative we deliver to judges is a real scientist's problem (manual media optimization is slow, error-prone, and intuition-limited) — and the hackathon demo is also the first pilot of the real product architecture.

## Product Vision

**Cell.ai is an AI scientist that designs, runs, and learns from cell culture experiments autonomously.**

A scientist tells Cell.ai: "I have this organism and these reagents — find the best growth media." Cell.ai reads the literature, designs the first experiment, sends it to the robot, reads the results, diagnoses problems in the data, updates its understanding, and designs the next experiment. The scientist reviews and steers. The robot executes. The AI thinks.

**Where the AI creates value no other tool can:**

| Capability | What it does | Why only LLM can do this |
|---|---|---|
| **Literature → constraints** | Reads papers, translates to search space rules: "NaCl + Glucose above X = osmotic stress, exclude" | BayBE doesn't read. Humans forget or miss papers. |
| **Data diagnosis** | Detects anomalies: "Blanks higher than samples — contamination or pipetting error. Excluding conditions 3, 7, 11 from learning." | Pipeline passes garbage to optimizer. LLM catches it. |
| **Search space adaptation** | Changes the experiment design between rounds: "Glucose >10 g/L consistently fails. Narrowing range, reallocating budget to NaCl exploration." | BayBE optimizes within fixed space. LLM changes the space. |
| **Zero-shot new organism** | Scientist says "now E. coli." LLM reads literature → starting recipe, ranges, constraints, known interactions — before any experiment. | BayBE starts from scratch. LLM starts from knowledge. |
| **Data → understanding** | "Optimal NaCl 22 g/L matches published optimum. Low glucose likely avoids acetate-driven pH crash. Recommend: test pH separately next." | BayBE outputs numbers. LLM outputs science. |

**The pattern:** BayBE optimizes *within* a search space. LLM operates *between* — between literature and experiment, between data and decision, between one organism and another, between numbers and understanding.

**Hackathon = first proof point.** 2-3 rounds on V. natriegens with the real LLM agent architecture — tools, reasoning, literature access. Enough to prove the loop works and AI finds better recipes than a scientist's intuition. At 10+ rounds, across organisms, over months, the value of reasoning between experiments compounds.

---

# 1. Description: What is it?

An autonomous AI agent that optimizes cell culture media for *Vibrio natriegens* in a closed loop on Monomer Bio's robotic workcell within a 24-hour hackathon.

- **Organism:** *V. natriegens* — fastest-growing non-pathogenic bacterium (~10 min doubling time)
- **Optimizing:** 3 media components — NaCl (10-35 g/L), Glucose (1-20 g/L), Yeast Extract (2-10 g/L)
- **Fixed:** Tryptone (10 g/L), MOPS buffer (pH 7) as fill-up solvent
- **Loop:** AI proposes 14 compositions → robot mixes → 2-4h incubation at 37°C → OD600 read → AI learns → next round
- **Scope:** up to 2-3 rounds in 10 hours of robot time (robots sleep at midnight)
- **Metric:** growth rate vs. initial recipe control
- **Format:** 96-well plate, 60 usable inner wells (outer wells = buffer against edge effects), 4 wells per condition (3 replicates + 1 blank)

> **Hackathon brief:** *"Build an autonomous workflow that iteratively varies media components, runs cell culture, measures outcomes, and updates the next experiment end-to-end. All on REAL cells."*

---

# 2. Problem: What problem is this solving?

**2a. How scientists optimize media today (without AI)**

A scientist has a bacterium (*V. natriegens*) and a starting media recipe (Tryptone, Yeast Extract, NaCl, Glucose in specific proportions). The cells grow on it, but it's unclear whether this recipe is optimal. The goal: find the combination of ingredient concentrations that maximizes growth rate.

The manual process:

1. **Design conditions.** The scientist picks variants based on experience, intuition, and literature: "let me try more NaCl here, less glucose there." With 3 components and meaningful ranges, there are hundreds of possible combinations. The scientist picks 10-15 to test.
2. **Prepare media.** For each variant, the scientist manually calculates volumes from stock solutions (g/L → µL), then pipettes each component into tubes. For 15 conditions — that's 60+ individual pipetting steps by hand.
3. **Plate cells.** Each variant media is dispensed into wells of a 96-well plate (200 µL per well), then a fixed amount of bacteria is added to each well (seeding).
4. **Incubate.** Plate goes into a 37°C incubator for 2-4 hours.
5. **Measure.** Plate goes into a plate reader that shines 600 nm light through each well. More turbid = more bacteria grew = higher OD600.
6. **Analyze.** Scientist calculates growth rates, compares to baseline, decides: "this combination worked better, that one didn't" — then goes back to step 1 and designs the next round of variants.

> *"I might have to have like 30 different samples which are each like a plate... but then I also manually have to make those individual media conditions and like pour them in every plate and like monitor all those plates... it's like a matrix, like you have to make huge matrices manually."* — Nikki, [37:37]

**2b. Where it breaks down**

| Step | Bottleneck | Impact |
|---|---|---|
| 1. Design | Human intuition limits exploration. Scientist picks "safe" variants, misses non-obvious interactions (e.g., NaCl × Glucose osmolarity effect). | Suboptimal search — hundreds of combinations untested. |
| 2. Prepare | 60+ manual pipetting steps per round. Calculation errors (g/L → µL) go unnoticed. | Hours of labor + human error in volumes = wrong media mixed. |
| 3-5. Execute | Each round takes a full afternoon: plate, incubate, measure. Scientist must be physically present. | 1-2 rounds/day max. Multi-day calendar time. |
| 6. Analyze | Scientist eyeballs results in Excel, picks next variants by gut. No systematic model of what worked and why. | Learning is implicit, not cumulative. Each round starts from scratch. |

> *"It's more like the manual labor piece... it's really like the amount of time it takes to set up so many different conditions."* — Nikki, [37:17]

The tools to fix each step exist separately — Bayesian optimization (BayBE), robotic liquid handlers (Opentrons), plate readers (Tecan) — but nobody has wired them into a single closed loop where the AI both designs experiments and learns from each round autonomously.

**2c. What problems are we NOT solving?**

- **Contamination detection** — takes days to manifest; can't demo in 24 hours.
- **Passaging / cell expansion** — requires dislodging cells; adds mechanical complexity outside scope.
- **Potency / functional characterization** — requires specialized assays beyond OD600.

---

# 3. Why: How do we know this is a real problem and worth solving?

**Market validation:**

- TetraScience's Media Formulation Assistant claims **88% fewer wet lab experiments**. Synthace has **94% ARR growth** in this space. BayBE-based optimization achieved **3-30x fewer experiments** than DOE (Nature Communications, 2025) and **181% more cells** than commercial media in cellular agriculture. The demand is proven; the startup-accessible closed-loop product doesn't exist yet.

**Speed gap:**

- A scientist can test ~50 conditions in a few hours manually — but each round requires calculating volumes, pipetting 60+ wells, waiting, reading, analyzing, and deciding what's next. The iterative part is what kills: 2-3 rounds takes days of calendar time.

> *"A person could test like 50 conditions in like three hours, but if this can spit it back faster and then do the iterative part — I think even like three times would be impressive because if I was in a lab it would take a lot longer than that."* — Nikki, [36:09]

**Novelty:**

- No published Bayesian optimization or DOE study on *V. natriegens* media exists. This work is genuinely novel — not reproducing known results, but generating new data.

---

# 4. Success: How do we know if we've solved this problem?

**Functional criteria — did it work?**

| Criteria | Minimum (ship it) | Strong (win) | Stretch |
|---|---|---|---|
| **Autonomous closed-loop rounds** (zero human intervention) | 2 | 2 | 3 |
| **Growth rate vs. initial recipe** (~2.0-2.5 h⁻¹ expected) | Any measurable gain (>2.5 h⁻¹) | >30% above baseline (~3.0+ h⁻¹) | >2x baseline (~4.0+ h⁻¹, approaching published max) |
| **Working demo** at Sunday 4:30pm | Loop ran, results shown | Live dashboard + narrative | Non-obvious finding the scientist didn't predict |

**Benchmark:** Initial recipe (10 g/L Tryptone, 5 g/L YE, 10 g/L NaCl, 0 g/L Glucose in MOPS pH 7). This is a sub-optimal LB-like medium with NaCl at 1% — below the published optimum of 1.5-2.5% (Long et al. 2019). Expected baseline growth rate: **~2.0-2.5 h⁻¹**. Published ceiling for *V. natriegens* in optimized complex media: **~4.4 h⁻¹** (Hoffart 2017).

**Winning criteria — what separates 1st place from "good job":**

| Criteria | Why it wins | How we deliver |
|---|---|---|
| **Live loop on stage** | Other team shows results; we show the process running. Judges remember what they *see*, not what they hear. | Pre-stage a round so it's actively running during demo. Dashboard shows real-time status. |
| **Biological insight** | "We optimized" is boring. "Our AI discovered that NaCl and Glucose interact non-linearly — high salt + high sugar crashes growth via osmotic stress" is a story judges retell. | Mine BayBE's surrogate model for interaction effects. Prepare 1-2 "the AI found something a human wouldn't" talking points. |
| **One slide, four numbers** | Judges see 10+ demos. They remember concrete numbers, not explanations. 48pt font, one line each. | (1) Best growth rate vs. baseline, (2) % improvement round-over-round, (3) rounds completed autonomously, (4) total conditions explored. |
| **Pre-recorded backup** | If live demo crashes, having nothing = catastrophe. A 60-second video of the loop running saves the pitch. | Record screen capture of a successful round before Sunday morning. |
| **"Autonomous science" framing** | Don't say "optimization tool." Say "AI scientist that designs its own experiments, runs them on a robot, and learns from the results." Judges fund visions, not utilities. | Pitch opens with: "What if an AI could run its own experiments?" — not "We built a BayBE wrapper." |

Success = the agent found a better media recipe than the scientist's starting point, and we can prove it with data at demo time. **But winning = we told a story the judges can't forget.**

---

# 5. Audience: Who are we building for?

**Primary: Hackathon judges** — scientists, engineers, and builders at the Monomer Bio event. They evaluate whether the agent demonstrates a credible, end-to-end autonomous workflow on real cells.

**Secondary: Cell culture scientists** — researchers who optimize media manually and want a system that answers: "I have these cells, I want this much growth — what recipe should I use, given the reagents I have?"

> *"I have these cells, I want to see this much growth — what cocktail would be good for that? Or how much quantity I should use of the individual components... like a recipe."* — Nikki, [31:32]

---

# 5b. Product Hypothesis & Hackathon Pilot

## Product hypothesis

**An LLM agent with access to scientific literature, Bayesian optimization, and robotic execution can design and run cell culture experiments better than a scientist working manually — and get better with each round because it reasons across experiments, not just within them.**

The core bet: LLM creates value at the *boundaries* that no other component covers:

| Boundary | What the agent does | What happens without it |
|---|---|---|
| Literature → Experiment | Reads papers, sets constraints and priors before round 1 | Human does this from memory, misses papers, forgets interactions |
| Data → Decision | Diagnoses anomalies, excludes bad data before optimizer learns | Garbage goes into BayBE, next round is based on noise |
| Round N → Round N+1 | Changes search space, narrows dead zones, reallocates budget | Fixed search space, optimizer wastes points on proven-bad regions |
| Organism → Organism | Zero-shot experiment design from literature for new organism | Start from scratch every time |
| Numbers → Understanding | Explains *why* a result happened, recommends next experiment | Scientist gets a spreadsheet |

**Falsifiable:** If the agent with LLM reasoning finds a better recipe in fewer rounds than BayBE-only pipeline — the hypothesis holds. If not — LLM overhead isn't worth it.

## Hackathon pilot — what we build to test this

The hackathon is the first test of this hypothesis. Not a throwaway demo — a real pilot of the real architecture.

**Architecture: LLM agent with tools**

```
LLM Agent (brain)
 ├── tool: suggest_compositions(space) → BayBE              [CORE]
 ├── tool: compile_recipe(g/L) → Compiler                   [CORE]
 ├── tool: run_experiment(layout) → Monomer MCP              [CORE]
 ├── tool: read_results() → Parser                           [CORE]
 ├── tool: diagnose_data(results) → anomaly checks           [CORE]
 ├── tool: update_search_space(ranges) → BayBE config        [STRETCH]
 └── tool: search_literature(query) → Elnora MCP             [ENHANCEMENT]
```

**Elnora is an enhancement, not core.** The agent must complete a full loop WITHOUT Elnora. If Elnora works — it adds literature-grounded constraints and differentiates the demo. If it doesn't — zero impact on the loop.

**What's real vs. simplified in the pilot:**

| Agent capability | Pilot (hackathon) | Full product | Pre-hack | Hack day |
|---|---|---|---|---|
| Calls tools in sequence | **Real** — LLM orchestrates, not hardcoded | Same | 3h (scaffold) | 1h (wire MCPs) |
| Reads literature for constraints | **Enhancement** — queries Elnora before round 1 | Deeper: cross-references, meta-analysis | 1h (research) | 1h (connect) |
| Generates hypothesis per round | **Real** — shown on dashboard | Same | 1h (prompt) | 1h (test live) |
| Diagnoses data anomalies | **Simplified** — checks blanks < samples, flags outliers | Full statistical QC, contamination detection | 1h | — |
| Adapts search space between rounds | **Stretch** — LLM narrows ranges if dead zones found | Automatic with confidence thresholds | — | 3h (if time) |
| Interprets results scientifically | **Real** — compares to literature, explains mechanisms | Same + cross-experiment memory | 1h (prompt) | 1h (test live) |
| Zero-shot new organism | **Not built** — V. natriegens only | Core product differentiator | — | — |
| | | | **7h** | **7h** |

**Fallback:** If LLM agent hangs or fails → human triggers tools manually via CLI. Same tools, same data, same results — just human-in-the-loop instead of agent-in-the-loop. Demo story becomes "AI-designed, human-triggered" rather than "fully autonomous."

## How we prove the hypothesis at the hackathon

**Test 1 — AI vs Human (same plate, same conditions):**

Round 1: 10 conditions from agent + 4 from Nikki + 1 control. Same incubation, same read. If agent's best > Nikki's best → agent adds value beyond human intuition.

**Test 2 — Agent reasoning is visible and correct:**

Agent generates hypothesis before round 2. After round 2, we check: did the hypothesis hold? If yes → agent reasons, not just optimizes. Shown live on dashboard.

**Test 3 — Loop completes autonomously:**

2 rounds with zero human intervention during the loop. Agent calls tools, handles results, proposes next round. If it works → architecture is viable.

## Demo differentiators (RICE-ranked)

| # | Idea | Effort | Why it wins |
|---|---|---|---|
| 1 | **Live debate: Nikki reacts to AI results on stage** | 2h prep | RICE 12.8. "I would never have tried this" = the moment we win. |
| 2 | **AI vs Human on same plate** | 3h build | RICE 8.0. Direct proof of value. Hero slide. |
| 3 | **AI generates hypotheses between rounds** | 4h build | RICE 5.3. "Scientist" not "optimizer." Visible on dashboard. |

---

# 6. What: Roughly, what does this look like in the product?

## Agent architecture

The LLM agent is the brain. Everything else is a tool it calls.

```
                         ┌─────────────┐
                         │  LLM Agent  │
                         │   (brain)   │
                         └──────┬──────┘
                                │
          ┌─────────────────────┼───────────┬──────────┐
          ▼                     ▼           ▼          ▼
   ┌──────────┐          ┌────────┐ ┌────────┐ ┌────────┐
   │  BayBE   │          │Compiler│ │Monomer │ │ Parser │
   │(optimizer)│          │(g/L→µL)│ │  MCP   │ │(OD→µ)  │
   └──────────┘          └────────┘ └────────┘ └────────┘
   suggest                translate   mix/plate/  blank sub
   compositions            volumes    incubate/   growth rate
                                      read
                  ┌────────┐
                  │ Elnora │ ← ENHANCEMENT (not on critical path)
                  │  MCP   │
                  └────────┘
                  literature
                  constraints
```

## Agent tools

**1. search_literature(query) → Elnora MCP [ENHANCEMENT]**
- 25 MCP servers: PubMed, KEGG, UniProt, etc.
- Agent calls *before round 1*: "What is known about V. natriegens NaCl tolerance?" → sets constraints
- Agent calls *when results are unexpected*: "Why would high glucose suppress growth in buffered media?" → finds acetate mechanism
- **Not on critical path.** Agent completes full loop without Elnora. If it works — differentiator. If not — zero impact.
- **Open question:** Exact endpoints Elnora exposes. Confirm with Carter Allen / Carmen Kivisild.

**2. suggest_compositions(search_space) → BayBE**
- Agent defines the search space (components, ranges, constraints). BayBE suggests compositions.
- Bayesian optimization with GP surrogate — balances exploration vs exploitation.
- Agent can *change* the search space between rounds based on reasoning.

**3. compile_recipe(composition_gL) → Compiler**
- Converts g/L concentrations to µL volumes for 1 mL media stocks.
- Validates: total = 1000 µL, every volume ≥10 µL (Opentrons minimum) or exactly 0 µL.
- Example — initial recipe:

| Stock | Calculation | Volume |
|---|---|---|
| Tryptone (100 mg/mL) | 10 g/L ÷ 100 mg/mL | 100 µL |
| Yeast Extract (100 mg/mL) | 5 g/L ÷ 100 mg/mL | 50 µL |
| NaCl (5M = 292.2 mg/mL) | 10 g/L ÷ 292.2 mg/mL | 34.2 µL |
| Glucose (100 mg/mL) | 0 g/L | 0 µL |
| MOPS pH 7 (fill-up) | 1000 − sum | 815.8 µL |
| **Total** | | **1000 µL** |

**4. run_experiment(plate_layout) → Monomer MCP**

| MCP Action | What it does |
|---|---|
| Create media mixture | Opentrons Flex mixes 1 mL of each composition from stocks |
| Media exchange | Dispenses 200 µL per well into assigned wells |
| Incubate | Moves plate to STX-220 (37°C, 2-4 hours) |
| Plate read | Tecan Infinite reads OD600 absorbance |

**5. read_results() → Parser**
- **Blank subtraction:** cell well OD600 − blank well OD600 = corrected OD600. Removes Glucose+NaCl particle artifacts.
- **Growth rate:** µ = ln(OD_corrected_final / OD_initial) / time_hours
- **Anomaly check:** flags conditions where blank > sample or corrected OD is negative.
- Owner: Arne.

**6. diagnose_data(results) → Agent reasoning**
- A lightweight tool that wraps the agent's own reasoning over parser output.
- Checks: are blanks consistent? Any outlier conditions? Does anything contradict the hypothesis?
- Can exclude bad data points before feeding to BayBE.

## Plate layout

**Round 1 — AI vs Human proof:**
```
    1  2  3  4  5  6  7  8  9  10 11 12
A  [------------ edge wells: buffer only ------------]
B  | A1r A1r A1r A1b | A2r A2r A2r A2b | A3  | A4  |
C  | A5r A5r A5r A5b | A6r A6r A6r A6b | A7  | A8  |
D  | A9r A9r A9r A9b | A10r ...         |     |     |
E  | H1r H1r H1r H1b | H2r H2r H2r H2b |     |     |
F  | H3r H3r H3r H3b | H4r H4r H4r H4b |     |     |
G  | CTL CTL CTL CTLb |                  |     |     |
H  [------------ edge wells: buffer only ------------]

A = AI (BayBE) conditions (10), H = Human (Nikki) conditions (4)
CTL = initial recipe control, r = replicate, b = blank
```

**Round 2+ — full AI budget:**
```
14 AI conditions + 1 control = 15 × 4 wells = 60 inner wells
```

- 60 usable inner wells (outer ring = buffer against edge effects)
- 4 wells per condition: 3 replicates + 1 blank
- 1 mL media prepared per condition (200 µL × 4 wells + 200 µL headroom)
- Fresh plate each round

## Dashboard (Streamlit) — what to show

| Panel | Data | Update |
|---|---|---|
| **Round status** | Current round, time remaining in incubation, which wells active | Live (30s refresh) |
| **Growth rate leaderboard** | Top 5 conditions by growth rate, ranked | After each plate read |
| **Round-over-round improvement** | Bar chart: best growth rate per round vs. initial recipe control | After each plate read |
| **AI vs Human** (round 1) | Side-by-side: agent's best vs. Nikki's best, with % difference | After round 1 read |
| **Agent hypothesis** | Text: what the agent expects before next round, what it found after | After each round |
| **Parameter space** | Scatter/parallel coordinates of NaCl × Glucose × YE tried so far | After each round |

Owner: Slava. Build pre-hack, test with mock data.

---

# 7-8. Timeline, Milestones & Experiment Plan

## Pre-hack (Mar 12-13)

| What | Owner | Risk | Done? |
|---|---|---|---|
| Agent tools: BayBE config, Compiler, Parser | Slava + Arne | Compiler volume math must be exact | |
| LLM agent scaffold: tool definitions, prompt, orchestration | Slava | First time building agent with these tools | |
| Streamlit dashboard: live status, hypothesis display, results comparison | Slava | | |
| Elnora MCP research: what endpoints, how to call | Slava | Elnora docs may be sparse. Confirm with Carter Allen / Carmen Kivisild | |
| Validate compiler: output matches scientist's hand calculation (100 µL Tryptone + 50 µL YE + 34.2 µL NaCl + 815.8 µL MOPS = 1 mL) | Arne + Nikki | | |
| Prepare Nikki's 4 conditions for AI vs Human (round 1) | Nikki | | |
| Record pre-recorded backup video of agent running in mock mode | Slava | | |

## Hack day (Saturday Mar 14)

| Time | What | Details |
|---|---|---|
| 9:30-12:00 | **Arrive + kickoff** | Check-in, kickoff, finalize teams |
| 12:00-1:00 | **Tutorial** | Monomer staff walks through seeding density experiment. Learn MCP command format, plate reader output format. |
| 1:00-2:00 | **Confirm + calibrate** | Verify stock concentrations from physical labels. Finalize plate layout. Test Elnora MCP endpoints (if available). Most parameters pre-resolved — this is validation, not discovery. |
| 2:00-4:00 | **Wire agent** | Connect agent to real Monomer MCP (core). Test: agent calls suggest_compositions → BayBE responds. Compiler → valid volumes. Try Elnora MCP (enhancement). **Expect 2h of setup friction.** |
| 4:00-4:30 | **Round 1 setup** | Agent calls BayBE → 10 AI conditions. (If Elnora available: queries for V. natriegens constraints first.) Add 4 Nikki conditions + 1 control. Compiler → µL. Robot mixes + plates. |
| 4:30-7:00 | **Round 1 incubation** | 2-4h at 37°C. Meanwhile: verify dashboard shows live status, test hypothesis generation prompt, prepare round 2 flow. |
| 7:00-7:30 | **Round 1 read + learn** | Plate read → Parser (blank subtraction + growth rate). Agent diagnoses data quality. Agent generates hypothesis. Agent compares AI vs Nikki conditions. Agent calls BayBE with results → round 2 suggestions. **Key moment: does AI beat Nikki?** |
| 7:30-8:00 | **Round 2 setup** | Agent may update search space based on round 1 reasoning (stretch). 14 AI conditions + 1 control on fresh plate. |
| 8:00-10:30 | **Round 2 incubation** | 2-4h at 37°C. Meanwhile: analyze round 1 data on dashboard, build demo narrative, rehearse Nikki's live reaction. |
| 10:30-11:00 | **Round 2 read + learn** | Parse, diagnose, interpret. Agent generates final summary. |
| 11:00-12:00 | **Round 3 (stretch)** | Only if round 2 done by 10:30. Robots sleep at midnight. |
| 12:00 AM+ | **Demo prep** | Compile results, finalize dashboard, polish narrative, record backup video, rehearse pitch. **Pitcher (Slava) sleeps 2-3 hours. Nikki preps "live reaction" talking points.** |

## Demo day (Sunday Mar 15)

| Time | What |
|---|---|
| Morning | Final dashboard polish. Rehearse pitch aloud 3x. Prepare "one slide, four numbers." |
| 3:00 PM | Final submission |
| 3:30-4:30 PM | Walk-around showcase |
| 4:30-5:30 PM | **Demo + pitch** |

**Demo script (2 min):**
1. **30s — Problem:** "Scientists spend days optimizing media by hand. We built an AI scientist that does it in hours."
2. **60s — Live demo:** Dashboard showing agent's rounds, hypothesis, results. AI vs Human comparison on screen. If possible: loop actively running.
3. **30s — Results + Nikki reaction:** "One slide, four numbers." Nikki: "I would never have tried this combination." → agent's biological explanation on screen.

**Fallback:** If live demo crashes → pre-recorded backup video (60s of agent running a full round).

## Milestones (go/no-go checkpoints)

| Checkpoint | Time | Go condition | No-go action |
|---|---|---|---|
| **Agent connects to MCPs** | Sat 4:00 PM | Agent calls Monomer MCP → gets response | Fallback: human triggers MCP commands, agent does design + analysis only |
| **Round 1 plate in incubator** | Sat 4:30 PM | Robot mixed + plated successfully | Debug with Monomer staff. Worst case: manually plate, agent still designs. |
| **Round 1 data is clean** | Sat 7:30 PM | Blanks < samples, growth rates positive, ≥10 valid conditions | Exclude bad conditions, proceed with partial data. Agent diagnoses issues. |
| **AI vs Human result** | Sat 7:30 PM | At least 1 AI condition beats Nikki's best | Still a valid result: "Scientist matched AI in round 1 — but AI improves in round 2, scientist can't." |
| **Round 2 complete** | Sat 11:00 PM | Agent completed 2 full rounds autonomously | 1 round + strong analysis is still a viable demo. Focus on reasoning quality. |
| **Demo ready** | Sun 3:00 PM | Dashboard works, pitch rehearsed, backup video ready | Cut features. Show what works. Never demo broken things. |

---

# 9. North Star Metric (NSM) Framework

**NSM: Best growth rate achieved vs. initial recipe control (absolute and %)**

Growth rate (not raw OD) is the target — OD600 → µ via ln(OD_final / OD_initial) / time. Anchored to on-plate basal control (initial recipe, 4 wells per plate) and external benchmark (published max ~4.4 h⁻¹, Hoffart 2017). Self-referencing "round 1 to final" is gameable — basal control is not.

## Metric Table

| Category | Metric | Target | Feeds |
|---|---|---|---|
| **NSM** | Best growth rate vs. initial recipe | See Section 4 targets | — |
| **Loop reliability** | Rounds completed autonomously (zero human intervention) | 2 min, 3 stretch | NSM prerequisite |
| **Agent reasoning** | Round N best > Round N-1 best | Improvement each round | Proves agent learns |
| **Agent reasoning** | Variance narrowing across rounds | Spread decreasing | Proves agent converges |
| **Agent vs. Human** | Agent's best vs. Nikki's best (Round 1 same plate) | Agent > Human | Proves agent value |
| **Throughput** | Total compositions tested in 24h | 28-42 (14/round × 2-3) | Story metric |

## Demo Slide — one slide, four numbers (48pt)

1. **Best growth rate vs. basal** — "Our AI's best recipe outperformed basal media by X%"
2. **Round-over-round improvement** — "Growth rate improved Y% from round 1 to round N"
3. **Rounds autonomous** — "N closed loops with zero human intervention"
4. **Compositions explored** — "Z unique media recipes designed, executed, and learned from"

---

# 10. Eval Framework — Pre-Hack Validation

**Principle:** Every eval tests a failure mode that would kill the demo. Two evals survive the cut.

### E1. Interface Contract Tests — "Do the tools fit together?"

**Failure mode:** Agent calls `suggest_compositions()` → BayBE output doesn't compile to valid volumes → MCP rejects the command → loop crashes at the seams.

**Method:**
- Generate 50 BayBE recommendations (NaCl 10-35 g/L, Glucose 1-20 g/L, YE 2-10 g/L)
- Feed each through `compile_recipe()` → verify volumes sum to 1000 µL, all volumes ≥10 µL (Opentrons minimum) or exactly 0 µL
- Feed compiler output through MCP command formatter → verify valid payload
- Feed simulated plate reader CSV through `read_results()` → verify blank subtraction, growth rate calculation, edge case handling (negative OD, empty wells, extra headers)

**Pass:** 100% compile, 100% format, parser handles all edge cases. **Build: 2h. Run: 5 min. Owner: Slava.**

### E3. Stateful MCP Mock — "Does the agent handle real robot behavior?"

**Failure mode:** Agent works against instant JSON mock but crashes against real MCP (latency, state requirements, transient failures, CSV output).

**Method:** Mock MCP that enforces:
- **State machine:** plate must be in correct location per operation (handler → incubator → reader)
- **Latency:** 5-30s per command (randomized)
- **Transient failures:** 5% of commands return retriable errors
- **Output format:** plate reader returns CSV with headers, not JSON

Run agent for 2 full rounds against this mock.

**Pass:** 2 rounds complete, retries work (≤3), correct command sequencing, CSV parsed, <30 min overhead per round. **Build: 3h. Run: 15 min. Owner: Arne.**

### Eval Schedule

| Day | Eval | Build | Run | Owner |
|---|---|---|---|---|
| Mar 12 | E1: Interface contracts | 2h | 5 min | Slava |
| Mar 13 | E3: Stateful MCP mock | 3h | 15 min | Arne |
| **Total** | | **5h** | **~20 min** | |

---

# 11. PRD Review — Resolved Summary

All critical issues from the initial PRD review have been resolved. Key decisions are embedded in Sections 1-9.

| # | Issue | Resolution | Where |
|---|---|---|---|
| 1 | World Model / Digital Twin is fantasy scope | Cut entirely. BayBE handles explore/exploit. | Section 6 |
| 2 | Timeline assumes zero setup friction | First plate at 4 PM. 2 rounds plan, 3 stretch. | Section 7-8 |
| 3 | No MCP fallback | "AI-designed, human-triggered" degraded mode defined. | Section 5b |
| 4 | Fresh plates unconfirmed | Confirmed by scientist sync Mar 11. | Section 7-8 |
| 5 | NSM measuring wrong thing | Anchored to basal control, not self-referencing. | Section 9 |
| 6 | OD proxy validity | V. natriegens is suspension — OD600 validated. | Section 1 |
| 7 | Compositions under-specified | 14 conditions + 1 control, scientist-confirmed. | Section 6 |
| 8 | No ownership / build plan | Slava (agent), Arne (parser/MCP), Nikki (biology). | Section 7-8 |

**Remaining risks:** (1) 2-4h incubation limits rounds — each must count. (2) Elnora MCP untested — build assuming optional. (3) Compiler volume math must be exact — validate against hand calculation.
