# PRD: AI-Driven Cell Culture Media Optimization Agent

**Project:** 24hr AI Science Cell Culture Hack @ Monomer Bio — Track A
**Date:** March 14-15, 2026
**Author:** Cell.ai team
**Status:** Draft

---

# 1. Description: What is it?

An autonomous AI agent that optimizes cell culture media composition in a closed loop on Monomer Bio's robotic work cell during a 24-hour hackathon. The agent uses an LLM to generate an initial media "recipe" from scientific literature for an unknown cell line (revealed morning-of), then uses Bayesian optimization to iteratively suggest new compositions. Each round, the robot mixes the media, applies it to cells in a 96-well plate, incubates, and reads outcomes via a plate reader. The results feed back into the optimization algorithm, which proposes the next set of compositions — repeating for 2-3 loops until the agent converges on the highest-yield formulation.

> **Hackathon brief:** *"Build an autonomous workflow that iteratively varies media components, runs cell culture, measures outcomes, and updates the next experiment end-to-end. All on REAL cells."*

---

# 2. Problem: What problem is this solving?

**2a. What is the problem this project addresses?**

- Cell culture scientists spend days of manual labor testing media formulations one-at-a-time — mixing, pouring, monitoring, and compiling results by hand — because no tool exists that can autonomously design, execute, measure, and iterate on media compositions in a closed loop on robotic hardware.

> *"It's more like the manual labor piece that's like the problem for all these iterative like hands-on stuff. It's not like reading results or comparing data isn't the issue — it's really like the amount of time it takes to set up so many different conditions."* — Nikki, [37:17]

**2b. What is your hypothesis for why this problem is happening?**

- Today's media optimization is a brute-force matrix exercise. A scientist testing 2 media types across 4 components manually prepares ~30 individual plates, pours media into each, monitors them over time, and compiles data into Excel. This is repeated across multiple rounds. The tools exist in pieces — Bayesian optimization libraries (BayBE, BoTorch), robotic liquid handlers (Opentrons), plate readers — but nobody has wired them into a single autonomous loop where the AI both designs and learns from each round.

> *"I might have to have like 30 different samples which are each like a plate that has my cells and my media with like the different condition, but then I also manually have to make those individual media conditions and like pour them in every plate and like monitor all those plates... it's like a matrix, like you have to make huge matrices manually in person with a bunch of different media."* — Nikki, [37:37]

**2c. What problems are you NOT solving?**

- **Contamination detection/remediation.** The team explicitly scoped this out. Contamination takes days to manifest, far beyond the 24-hour hackathon window, and would require different instrumentation.

> *"The contamination I don't think we can do much about... I don't think it's like within 24 hours and is really hard."* — Team member, [05:48]

- **Passaging / cell expansion workflows.** Passaging requires dislodging cells, which adds mechanical complexity outside the scope of this demo.

> *"Is the experiment just from seeding till confluence, or do we also have a passaging aspect? Passaging is harder because now you need to dislodge the cells."* — Nikki, [06:24]

- **Cell potency or functional characterization.** The team will focus on simple health metrics (viability, growth) rather than complex functional readouts like potency or phenotype.

> *"The health ones are probably a lot easier, right? Like if they're alive, if they're growing, it's just simpler. The other ones get a little complicated."* — Nikki, [28:06]

---

# 3. Why: How do we know this is a real problem and worth solving?

**Business Impact:**

- TetraScience's Media Formulation Assistant claims to **reduce wet lab experiments by up to 88%** — validating that AI-driven media optimization has massive efficiency gains. Synthace has **94% ARR growth** serving this same need at enterprise scale. The market demand is proven; the startup-accessible product doesn't exist yet.

- BayBE-based approaches have been published in Nature Communications (2025), achieving results using **3-30x fewer experiments** than standard DoE methods, and in cellular agriculture research achieving **181% more cells** than commercial media variants while using **38% fewer experiments**.

- The hackathon itself is evidence: Monomer Bio, Opentrons, and multiple AI partners have organized a 50-builder event (fifth in the series) specifically around this problem space, signaling industry urgency.

> **Hackathon page:** *"For the fifth hack in this series, we're hosting another cell culture hack that brings together the Bay Area's AI, science, and engineering communities. Teams will have access to the latest AI tools for building agents and are given the opportunity to ship on Monomer's robotic workcell and individual walk-up instruments."*

**Customer Impact:**

- Scientists currently spend hours to days on what is fundamentally manual labor — mixing, pouring, monitoring plates — rather than on scientific thinking. The bottleneck is not analysis, it's physical setup.

> *"A person could test like 50 conditions in like three hours, but like if this can spit it back faster and then do the iterative part — I think even like three times would be impressive because if I was in a lab it would take a lot longer than that."* — Nikki, [36:09]

- Media formulation is a multi-variable optimization problem with real trade-offs (e.g., growth vs. potency) that scientists currently navigate by intuition and literature review, not systematic experimentation.

> *"The same mechanism that stimulates them exhausts them. So if you want something to grow rapidly, it's always like a pro-con situation."* — Nikki, [26:33]

- The quality of optimization is limited by what the scientist can manually test. Garbage-in-garbage-out is the primary risk — if the initial guess is bad, all downstream conditions suffer.

> *"It's as good as the inputs. If for some reason what we thought wasn't correct or the best approach, then you have a bunch of options but none of them are good."* — Nikki, [40:43]

---

# 4. Success: How do we know if we've solved this problem?

Given the 24-hour hackathon constraint, success is defined as:

- **Complete at least 2-3 closed-loop optimization rounds** end-to-end (AI suggests composition -> robot mixes -> incubate -> plate read -> AI learns -> next round) with zero human intervention during each loop.

- **Demonstrate measurable improvement** in the target metric (likely optical density as a proxy for cell growth/viability) from round 1 to round 2-3, showing the AI agent learned from prior results.

- **Deliver a working demo** at Sunday 4:30pm showcase: the agent receives a mystery cell line, autonomously generates an initial media recipe from literature, executes iterative optimization on the robotic work cell, and presents a final "best recipe" with supporting data.

- **Stretch goal:** The AI agent converges on a formulation that **outperforms a naive/literature-only baseline** — demonstrating that closed-loop optimization adds value beyond a single LLM literature lookup.

> *"I think even like three times would be impressive because if I was in a lab it would take a lot longer than that."* — Nikki, [36:36]

---

# 5. Audience: Who are we building for?

**Primary: Hackathon judges and demo audience** — scientists, engineers, and builders at the Monomer Bio event who will evaluate whether the agent demonstrates a credible, end-to-end autonomous workflow on real cells.

**Secondary: Cell culture scientists** (the long-term Cell.ai user) — researchers who currently optimize media manually, want to test more conditions faster, and need a system that handles the tedious matrix of mix-pour-monitor-compile. As described in the meeting:

> *"I have these cells, I want to see this much growth — what cocktail would be good for that? Or how much quantity I should use of the individual components... like a recipe."* — Nikki, [31:32]

They need a system constrained by what's actually available in their lab:

> *"You basically have some something and something you don't have, so you want to limit the answer by what components you have right now."* — Team member, [32:37]

---

# 6. What: Roughly, what does this look like in the product?

![Architecture Diagram](../assets/architecture-proposed.png)

The system has six components wired into an autonomous feedback loop:

**A. Input: Cell Type + Available Media Components**
- The mystery cell line is revealed morning-of. The scientist (or agent) specifies cell type and which media components are physically available on the robotic work cell.

**B. LLM Layer — Literature-Informed Priors**
- Standard Bayesian optimization starts with random guesses. Instead, an LLM agent reads scientific protocols and papers to set informed priors — generating a starting recipe grounded in published data for the given cell type.
- This dramatically reduces the number of wet-lab rounds needed by starting from a plausible region of the search space rather than random.

> *"We will put LLM who will go in literature for this cell type and will suggest something. So we need initial, we need this first one."* — Team member, [23:45]

**C. Bayesian Optimization Engine**
- Takes the LLM-generated starting recipe and generates a batch of ~8-12 variant compositions (one per row of a 96-well plate, with replicates across columns).
- After each round's results come back, the algorithm learns which compositions performed best and proposes the next batch.

> *"There is an algorithm which can optimize parameters... for example 12 different combinations. We create these combinations, we exchange media, we incubate, we measure something and put these results back in the algorithm, which now learns from our previous composition — which one worked, which did not — and now it gives us another set of assumptions."* — Team member, [24:14]

**D. World Model (Digital Twin / Simulator)**
- Before committing real reagents, the optimizer can "dream" — simulating thousands of candidate media recipes in silico to prune bad ideas before they reach the robot.
- Requires historical data or a learned model from prior rounds to be effective. In round 1 this layer is thin; by round 2-3 the agent has enough real data to build a predictive model that filters candidates.
- This is the key differentiator from a naive closed loop: the agent doesn't just try the next best guess, it pre-screens candidates computationally to maximize the value of each expensive wet-lab round.

**E. Automated Experiment via MCP**
- Only the simulator-vetted recipes reach the robot. The agent sends commands to Monomer's robotic work cell through MCP (Model Context Protocol):
  - **Create media mixture** — robot mixes the specified composition
  - **Media change** — robot applies the new media to wells
  - **Incubate** — robot moves plate to incubator for the required time (~4 hours per round)
  - **Plate read** — robot reads optical density or other signal as the outcome metric

> **Hackathon brief:** *"Robotic workcell actions are made available via MCP: 🌡️ Incubate, 🧪 Create media mixture, 💧 Media change, 🔬 Plateread."*

**F. Data Parser + Agent Learning**
- Raw plate reader output is parsed into structured results.
- The agent compares predicted outcomes (from the world model) against actual measurements, updates its internal model, and feeds everything back into the Bayesian optimizer for the next round.
- The feedback loop closes: **Input -> LLM Priors -> BayesOpt -> Simulator -> Robot -> Parse -> Learn -> BayesOpt -> ...**
- Output: the optimized recipe with the best measured outcome across all rounds.

> *"We have a feedback loop. We were like cooking and then we see a result, and the result is coming back in the way we can determine what part of the recipe was wrong."* — Team member, [35:15]

**Plate layout strategy:**
- 96-well plate: each row = a different media composition, columns = biological replicates.
- Reserve 1-2 wells per plate for basal media control — zero-cost addition that provides the external baseline for the North Star metric.
- Fresh plate for each optimization round to avoid carryover effects confounding the results.

> *"If we will be reusing the same plate for a second loop, there is no actually valuable data because it can be affected by previous [conditions]. Yeah, there's no control if you put it on the same group of cells."* — Team member & Nikki, [21:23]

**Measurement approach:**
- Primary: optical density via plate reader (available, automated, quantitative).
- The specific readout depends on cell type (adherent vs. suspension) and plate reader capabilities — to be confirmed with organizers.

> *"How about optical density — is it giving any valuable information? Yeah, I mean we have a plate reader. So that makes sense."* — Team discussion, [11:32]

---

# 7. How: What is the experiment plan?

**Phase 1: Pre-hack preparation (before Mar 14)**
- Build the optimization pipeline: LLM literature agent + BayBE/BoTorch Bayesian optimizer + MCP client for robotic commands.
- Prepare a cell-type-agnostic framework: when the mystery cell line is revealed, the LLM generates the initial recipe and the optimizer adapts automatically.
- Confirm with organizers (via Jimmy): what cell type, what plate reader capabilities, what media components are available.

> *"The biggest unknown is actually what components are available, what can we change, what agents do we have to play with — and then the equipment."* — Team member, [25:28]

**Phase 2: Hack day execution (Mar 14, 9:30am - Mar 15, 3pm)**
- **Hour 0-1:** Cell line revealed. LLM generates initial recipe from literature. Team configures available components and concentration ranges.
- **Hour 1-2:** Algorithm generates first batch of ~8-12 compositions. Robot mixes and plates.
- **Hour 2-6:** Incubation round 1 (~4 hours based on expected doubling time). Team monitors.
- **Hour 6-7:** Plate read round 1. Results feed into optimizer. Algorithm proposes round 2 compositions.
- **Hour 7-11:** Round 2: mix, plate, incubate, read.
- **Hour 11-15:** Round 3 (if time permits): mix, plate, incubate, read.
- **Hour 15-18:** Compile results, prepare demo narrative and dashboard.

> *"The cells... they grow in four hours and we can do several loops."* — Team member, [01:04]
>
> *"Two loops, three maximum. I don't know if somebody would like to stay overnight there."* — Team member, [20:09]

**Phase 3: Demo (Mar 15, 4:30-5:30pm)**
- Present the full closed-loop story: mystery cell line -> LLM-generated initial recipe -> iterative optimization -> final best formulation, with data showing improvement across rounds.

---

# 8. When: When does it ship and what are the milestones?

| Milestone | Date | Risks | Mitigations |
|---|---|---|---|
| **Confirm cell type, plate reader specs, and available media components with organizers** | ASAP (before hack) | Organizers may not respond in time; mystery cell line may not be revealed until morning-of | Reach out to Jimmy via email/LinkedIn now. Build cell-type-agnostic framework so the system works regardless. |
| **Optimization pipeline built and tested (LLM + BayBE + MCP client)** | Mar 13 (day before hack) | MCP interface may not be documented until event; BayBE integration may have edge cases | Use mock MCP endpoints for pre-testing. Have fallback to manual MCP commands if API integration fails. |
| **Round 1 complete (first plate read results in)** | Mar 14, ~4pm | Incubation takes longer than expected; plate reader output format unknown | Plan for 4-hour incubation windows. Have parsing scripts ready for common plate reader output formats. |
| **Round 2 complete (demonstrable learning)** | Mar 14, ~10pm | Cells may not show measurable differences between compositions in one round | Choose a metric (OD) with enough sensitivity. Ensure enough replicates per condition for statistical signal. |
| **Round 3 complete (stretch goal)** | Mar 15, ~6am | Requires overnight presence; cell viability may degrade | Optional milestone. Even 2 rounds with clear learning is a strong demo. |
| **Demo-ready** | Mar 15, 3pm (submission deadline) | Dashboard not polished; narrative unclear | Reserve last 3 hours exclusively for demo prep. Prioritize the "story" over the "polish." |

> **Hackathon agenda:** *"Saturday 9:30a Check in + breakfast. 10:00a Kickoff. 11:00a Finalize teams. 12:00p Hack + build #1. 6:00p Dinner + Round table talks. 7:00p Hack + build #2. 12:00a Robots go to sleep. Sunday 3p Final submission. 3:30-4:30p Walk around showcase. 4:30-5:30p Demos + Pitching."*

---

# 9. North Star Metric (NSM) Framework

## Hackathon NSM

**Best OD achieved across all rounds vs. basal media control (absolute and %)**

This is the single metric that answers the question judges will ask: "Did the AI find something genuinely good?" It is measurable directly from plate reader data, requires only reserving 1-2 wells per plate for basal media (zero-cost), and provides external validity — the AI's best recipe is compared against an independent baseline, not against its own starting point.

Round-over-round improvement remains a valuable supporting metric (it tells the learning story), but the North Star must be anchored to an external control. A self-referencing metric like "round 1 to final round improvement" can be inflated by a deliberately poor starting recipe — judges will see through this.

**Basal media definition:** Standard recommended media for the given cell type without optimization (e.g., DMEM + 10% FBS for common mammalian lines). This ensures the baseline is credible and non-gameable.

---

## Input Metrics

### Loop Reliability — did it actually run?

| Metric | Target | Why it matters |
|---|---|---|
| Rounds completed end-to-end with zero human intervention | 2 minimum, 3 stretch | If the loop breaks, nothing else matters. Operational prerequisite, not the goal. |

### AI Quality — did the optimizer make smart choices?

| Metric | Target | Why it matters |
|---|---|---|
| Best OD in round N vs. best OD in round N-1 | Measurable improvement each round | Feeds the North Star directly. If round 2 doesn't beat round 1, the AI didn't learn. |
| Variance across compositions within a round | Spread narrowing as rounds progress | If all compositions perform the same, the optimizer isn't exploring meaningfully. Narrowing spread = agent converging. |

### LLM Prior Quality — was the starting point intelligent?

| Metric | Target | Why it matters |
|---|---|---|
| Round 1 best OD vs. basal media reference (1-2 wells) | Round 1 best meaningfully above worst | Proves the LLM didn't just guess randomly. Reserve 1-2 wells for basal media as a sanity check — low cost, high storytelling value. |

### Speed — was it faster than manual?

| Metric | Target | Why it matters |
|---|---|---|
| Total compositions tested across all rounds in 24h | 24-36 (8-12 per round × 2-3 rounds) | The story isn't "we tested more" — it's "we tested smarter, with zero human hands." |

---

## NSM Tree

```
                        NORTH STAR
            Best OD vs. basal media control
                           |
            _______________|___________________________
            |               |                         |
        LOOP             AI QUALITY                STORY
        RELIABILITY
                                                   
        Rounds           Best OD per              Round-over-round
        completed        round                    OD improvement
        autonomously     (improving?)             (learning curve)
                                                   
        Zero human       Variance                 Total
        interventions    convergence              compositions
        per loop         across rounds            tested in 24h
```

---

## Demo Metrics — what to show the judges

One slide, four numbers:

1. **Best OD vs. basal** — "Our AI's best recipe outperformed basal media by X%" *(the North Star)*
2. **OD improvement** — "Cell growth improved Y% from round 1 to round N" *(the learning story)*
3. **Rounds completed autonomously** — "Our agent ran N closed loops with zero human intervention"
4. **Compositions explored** — "The system designed, executed, and learned from Z unique media recipes in 24 hours"

---

## Hackathon Targets

| Metric | Minimum | Strong | Stretch |
|---|---|---|---|
| North Star (best OD vs. basal control) | Any measurable gain | >30% above basal | >2x basal |
| Rounds completed autonomously | 2 | 3 | 3 + overnight |
| Rounds to beat baseline | ≤3 | 2 | 1 (LLM alone wins) |
| Human interventions per loop | 0 | 0 | 0 |

---

## Post-Hackathon Transition

Once Cell.ai moves into real pilots with scientists, the North Star shifts to: **% yield improvement over scientist's baseline per campaign, achieved in ≤3 rounds.** This adds the proper external control group that hackathon conditions cannot accommodate. Everything built during the hackathon feeds directly into this long-term NSM.

---

## Open Questions

These were explicitly identified during the team meeting as blockers requiring information from the organizers:

1. **What cell type?** The experiment design (adherent vs. suspension, doubling time, known media requirements) depends entirely on this.

> *"Did you guys say you know what cell type it is?" / "I don't know what it is." / "This is probably something that we need to reach out to them about."* — Team discussion, [04:49]

2. **What media components are available?** The optimization search space is constrained by what Monomer physically has on-site.

> *"What is the biggest unknown is actually what components are available, what can we change."* — Team member, [25:40]

3. **What does the plate reader measure?** Optical density, impedance, fluorescence — the measurement capability determines what the agent optimizes for.

> *"I just don't know like what the plate reader is doing is the other problem. If you know what it can do then it's probably easy for us to come up with something simple to look at."* — Nikki, [30:23]

4. **Fresh plate per round or reuse?** Team leaning toward fresh plates to avoid carryover confounds, but this depends on cell/plate availability.

> *"If we will be reusing the same plate for a second loop, there is no actually valuable data because it can be affected by previous [conditions]."* — Team member, [21:23]

---

## Key Design Decisions from Meeting

| Decision | Resolution | Rationale |
|---|---|---|
| Contamination track | Out of scope | Takes days to manifest; can't demo in 24 hours |
| Passaging | Out of scope | Adds mechanical complexity; focus on seeding-to-growth |
| Optimization target | Cell growth / viability (not potency) | Simpler to measure; potency requires functional assays |
| Measurement method | Plate reader (optical density) | Available via MCP; quantitative; automated |
| Initial media recipe | LLM literature search | No starting media provided; AI generates first guess |
| Plate strategy | Fresh plate per round (preferred) | Avoids carryover confounding results |
| Number of loops | 2-3 in 24 hours | ~4 hour incubation per round; overnight stay optional |

---

# 10. Eval Framework — Pre-Hack Validation

The NSM framework (Section 9) defines what success looks like on March 15. This section defines how we know the system works on March 13 — before we touch real cells, real robots, or real reagents.

**Principle:** Every eval tests a specific failure mode that would kill the demo. If an eval doesn't map to a demo-killing failure, cut it.

---

## 10.1 Eval Categories (Priority Order)

### E1. Interface Contract Tests — "Do the pieces fit together?"

**Failure mode:** LLM output doesn't parse into BayBE input. BayBE output doesn't map to MCP commands. Plate reader output doesn't feed back into BayBE. The system works component-by-component but crashes at the seams.

**Method:**
- Generate 50 LLM recipes using the actual prompt and 10 different cell types.
- Feed each through the exact parser that BayBE will consume.
- Feed BayBE's output through the exact formatter that produces MCP commands.
- Feed simulated plate reader CSV through the exact parser that returns results to BayBE.

**Pass criteria:**
- 100% of LLM outputs parse without error into valid BayBE search points.
- Every component name in LLM output maps to a component in BayBE's search space definition.
- Every concentration is a numeric value within the defined search bounds.
- Every BayBE suggestion produces a valid MCP command payload.
- Plate reader CSV parser handles: empty wells, negative values, missing rows, extra header lines.

**Time budget:** 2 hours to build, 5 minutes to run.

---

### E2. Noisy Convergence — "Does BayBE actually learn on realistic data?"

**Failure mode:** BayBE converges beautifully on a clean synthetic function, then falls apart when real biological noise enters the picture.

**Method:**
Build a biologically realistic synthetic objective:
- 4-5 media components with non-linear dose-response curves
- Interaction effects between components (e.g., glutamine × glucose)
- Toxicity cliffs above realistic thresholds
- 20% coefficient of variation (lognormal noise on every measurement)
- 5% outlier rate (garbage reads from bubbles, edge effects)

Run BayBE against this function for 3 rounds of 12 compositions each. Repeat 100 times with different random seeds.

**Pass criteria:**
- In ≥80 of 100 runs, the best composition in round 3 is within 30% of the true optimum.
- In ≥90 of 100 runs, best OD improves from round 1 to round 3.
- Mean number of rounds to find a composition >2× basal equivalent: ≤2.

**Fail investigation:** If <80% convergence, check:
- Is the search space too wide? Narrow concentration ranges.
- Is BayBE's kernel appropriate for the noise level?
- Are outliers poisoning the surrogate model? Add outlier filtering.

**Time budget:** 3 hours to build (most time on the synthetic function), 10 minutes to run 100 trials.

---

### E3. Stateful MCP Mock — "Does the agent handle real robot behavior?"

**Failure mode:** The mock MCP returns instant JSON responses. The real MCP has latency, state requirements, transient failures, and CSV output.

**Method:**
Build a mock that enforces:
- **State machine:** plate must be in the correct location for each operation (handler → incubator → reader). Out-of-order commands return errors.
- **Realistic latency:** 5-30s per command (randomized).
- **Transient failures:** 5% of commands return retriable errors.
- **Realistic output format:** plate reader returns CSV with headers, not clean JSON.

Run the full agent loop (LLM → BayBE → MCP → parse → BayBE) against this mock for 2 rounds.

**Pass criteria:**
- Agent completes 2 full rounds without crashing.
- Agent retries transient MCP failures (≤3 retries) before alerting.
- Agent correctly sequences commands (never sends plate_read before incubate completes).
- Agent parses CSV plate reader output into the correct data structure.
- Total non-incubation overhead per round: <30 minutes wall-clock.

**Time budget:** 3 hours to build, 15 minutes to run.

---

### E4. Decision Quality — "Does the agent make reasonable choices on weird data?"

**Failure mode:** The agent gets ambiguous or broken data and makes a catastrophic next move — doubling down on an outlier, panicking on flat results, or crashing on missing data.

**Method:**
Inject specific data scenarios after round 1 and verify the agent's round 2 proposal is reasonable:

| Scenario | Injected data | Expected behavior |
|---|---|---|
| Flat signal | All 12 compositions: OD 0.30 ± 0.02 | Increase exploration diversity; do not converge |
| Single outlier | 11 compositions: OD 0.3, one: OD 1.8 | Include 2-3 compositions near the outlier + diverse exploration; not all-in |
| Regression | All round 2 ODs worse than round 1 | Explore new region of search space; do not re-propose round 2 compositions |
| Negative values | 3 wells return OD -0.05 | Exclude negatives from optimization; do not crash |
| Missing data | 3 of 12 wells return NaN/empty | Exclude missing wells; optimize on remaining 9 |
| All wells excellent | All 12 compositions: OD > 1.0 | Narrow search around top 3-4; exploitation mode |

**Pass criteria:**
- Agent does not crash on any scenario.
- Agent's round 2 proposal is reviewed by a team member and judged "reasonable" for each scenario. (Manual review is acceptable — this is a judgment call, not an automated metric.)

**Time budget:** 2 hours to build scenarios, 30 minutes to review outputs.

---

### E5. End-to-End Timing — "Can we finish in time?"

**Failure mode:** Non-incubation overhead (recipe generation, MCP commands, data parsing, optimization) eats into the limited hackathon hours and costs us a round.

**Method:**
Run the full pipeline against the stateful MCP mock (E3) for 3 rounds. Measure wall-clock time for each step:

| Step | Budget |
|---|---|
| LLM recipe generation | < 30 seconds |
| BayBE batch generation | < 60 seconds |
| MCP command execution (all 12 compositions) | < 15 minutes |
| Plate reader parse + data formatting | < 60 seconds |
| BayBE update + next batch proposal | < 60 seconds |
| **Total non-incubation overhead per round** | **< 20 minutes** |

**Pass criteria:**
- Total overhead per round < 20 minutes (gives 10-minute buffer before the 30-minute concern threshold).
- No single step takes >2× its budget.

**Time budget:** 0 hours incremental (uses E3 mock; just add timing instrumentation).

---

### E6. Graceful Degradation — "What happens when something dies?"

**Failure mode:** One component fails completely, and the entire system crashes instead of entering a degraded mode.

**Method:**
For each component, simulate total failure and verify fallback:

| Component down | Expected fallback |
|---|---|
| LLM API unreachable | Use cached default recipe (DMEM + 10% FBS + standard supplements) |
| BayBE throws exception | Fall back to Latin Hypercube sampling (random-but-space-filling) |
| MCP unreachable for >5 min | Alert human operator; queue commands for retry; log state for manual execution |
| Plate reader returns empty | Alert human operator; do not feed empty data to BayBE |

**Pass criteria:**
- Agent does not crash on any total-failure scenario.
- Agent enters the defined fallback mode within 60 seconds of failure.
- Agent logs a clear, human-readable alert for each failure.

**Prerequisite:** Define the fallback behaviors in code BEFORE writing this eval. If fallbacks don't exist, this eval will fail by definition — which is the point.

**Time budget:** 1 hour to build, 10 minutes to run.

---

### E7. LLM Recipe Quality — "Is the starting point sane?"

**Failure mode:** The LLM hallucinates a media recipe with toxic concentrations, imaginary components, or nonsensical ratios.

**Method:**
- Generate recipes for 10 well-known cell lines (HEK293, CHO, HeLa, Jurkat, A549, MCF-7, iPSC, MSC, Vero, NIH/3T3).
- Compare each recipe against published protocols from ATCC / cell line provider datasheets.

**Pass criteria:**
- ≥60% of suggested components match published protocol components.
- No concentration exceeds 10× the published recommended range.
- No recipe contains components absent from a curated "real supplement" list (catches hallucinated reagent names).

**Why this is lowest priority:** Biological errors in round 1 are caught by the scientist reviewing the recipe morning-of. A bad LLM recipe wastes one round but doesn't crash the system. Interface bugs and MCP failures crash the system.

**Time budget:** 1 hour to build, 5 minutes to run.

---

## 10.2 Eval Validation — "Do the evals themselves work?"

An eval that passes everything is worse than no eval — it gives false confidence. Before trusting the suite:

### Mutation testing (mandatory, 30 minutes)

Inject 5 known bugs into the system. Run the full eval suite. Verify each bug is caught by at least one eval.

| Mutation | Expected to be caught by |
|---|---|
| LLM outputs string concentrations ("10%") instead of floats | E1 |
| BayBE always returns the same 12 compositions regardless of input | E4 |
| MCP commands sent out of order (plate_read before incubate) | E3 |
| Double all MCP response latencies | E5 |
| Plate reader parser returns zeros for all wells | E4, E6 |

**Pass criterion:** All 5 mutations are caught. If any passes through undetected, fix the eval before trusting it.

### Known-good / known-bad sanity check (mandatory, 10 minutes)

- **Known-good:** DMEM + 10% FBS recipe for HEK293 cells. Synthetic function tuned so this is near-optimal. All evals should pass.
- **Known-bad:** Empty recipe (all concentrations = 0). All content/convergence evals should fail.

If the known-bad input passes any eval, that eval's threshold is too loose.

---

## 10.3 Pre-Hack Eval Schedule

| Day | Eval | Build time | Run time | Owner |
|---|---|---|---|---|
| Mar 11 | E1: Interface contracts | 2h | 5 min | TBD |
| Mar 11 | E2: Noisy convergence | 3h | 10 min | TBD |
| Mar 12 | E3: Stateful MCP mock | 3h | 15 min | TBD |
| Mar 12 | E4: Decision quality | 2h | 30 min | TBD |
| Mar 13 | E5: Timing (uses E3) | 0h | 5 min | TBD |
| Mar 13 | E6: Graceful degradation | 1h | 10 min | TBD |
| Mar 13 | E7: LLM recipe quality | 1h | 5 min | TBD |
| Mar 13 | Mutation testing + sanity | 0.5h | 15 min | TBD |
| **Total** | | **12.5h** | **~1.5h** | |

Build cost: 12.5 hours across 3 days (Mar 11-13). Run cost: ~1.5 hours for the full suite. Re-run on hack morning after final config: 30 minutes.

---

## 10.4 What We Are NOT Evaluating

- **Biological correctness of results.** We cannot validate whether the optimized recipe is biologically meaningful without real cells. The evals validate that the system operates correctly, not that biology cooperates.
- **Incubation outcomes.** We cannot simulate cell growth. The synthetic function is a stand-in for testing the optimization loop, not a prediction of real results.
- **Demo narrative quality.** The story we tell judges is a human problem, not a system problem. No eval for this.

---

# 11. PRD Review — Critical Assessment

## Red Flags — Things that will hurt on March 14

### 1. The "World Model / Digital Twin" (Component D) is fantasy scope for a 24-hour hack

With 2-3 wet lab rounds and only 8-12 data points after round 1, there is not enough data to build a meaningful surrogate model in a high-dimensional space. The PRD says "In round 1 this layer is thin" — it's not thin, it's nonexistent, and by round 2 there still isn't enough data for it to matter. This component will eat engineering hours for zero demo value.

**Action:** Cut it entirely. BayBE's acquisition function already handles explore/exploit without a separate simulator layer. Every hour spent on a "world model" is an hour not spent on MCP integration reliability, which is where hacks actually fail.

### 2. The timeline assumes zero setup friction — the #1 killer

Phase 2 says "Hour 0-1: Cell line revealed, LLM generates recipe, team configures components." In reality, Hour 0-3 at these hacks is: figuring out MCP authentication, debugging why the liquid handler won't respond, discovering the plate reader output format is different than expected, realizing the available media components don't match what the LLM suggested. Getting the first plate into the incubator before Hour 3-4 would be exceptional.

**Action:** Plan for first plate-in-incubator at Hour 4. That gives two rounds max, not three. Build the "minimum viable demo" narrative around 2 rounds. Three is a stretch goal, not the plan.

### 3. No fallback plan for when MCP breaks

The entire system depends on four MCP endpoints that Monomer provides. The milestones table mentions "Have fallback to manual MCP commands if API integration fails" — but what does that actually mean? If MCP is down, the entire autonomous loop is dead.

**Action:** Define a concrete fallback: "If MCP is unavailable, manually trigger each robot action via Monomer's UI while the AI agent still handles composition design, data parsing, and optimization. The demo story becomes 'AI-designed, human-triggered' rather than 'fully autonomous.'" This is still a compelling demo and prevents a total wipeout.

### 4. "Fresh plate per round" is stated as preferred but not confirmed

If the organizers only provide one plate, or if cells aren't pre-seeded and ready, the entire experimental design collapses. This is listed as an open question but treated as a resolved decision in the design section — these are contradictory.

**Action:** Design for both scenarios NOW. Fresh plates: current design. Same plate: different plate layout with reserved control wells and carryover accounting. Have both configurations ready to deploy morning-of.

---

## Yellow Flags — Structural issues

### 5. ~~The NSM is measuring the wrong thing~~ RESOLVED

**Fixed in Section 9.** NSM updated from self-referencing "OD improvement round 1 to final" to externally-anchored "Best OD vs. basal media control." Basal control wells (1-2 per plate) added to plate layout. Demo metrics reordered to lead with the North Star. Round-over-round improvement retained as a supporting input metric for the learning story.

### 6. OD as a proxy for growth is not universally valid

For adherent cells, OD readings are notoriously noisy because cells stick to the bottom and don't scatter light uniformly. For suspension cells, OD works well. Since the cell type is unknown, the PRD needs a contingency plan for adherent cells — possibly using a confluence-based imaging readout if available, or at minimum acknowledging the limitation and describing how to handle it.

### 7. 8-12 compositions per round is under-specified

How many media components are being varied? What are the concentration ranges? BayBE needs a defined search space. The PRD hand-waves this as "configured morning-of" but search space design is the hardest part. With 6 components at 5 concentration levels, that's 15,625 possible combinations. 8-12 points per round across 2 rounds means sampling 0.1% of the space. BayBE configuration (kernel choice, acquisition function, priors from the LLM) matters enormously and needs to be pre-built and tested, not improvised.

**Action:** Add a section on search space design. Define: max components (cap at 4-5 for a hack), concentration range strategy (e.g., +/- 50% around LLM-suggested baseline), and how BayBE priors are initialized from the LLM output.

### 8. The architecture has six components but no ownership or build plan

Who builds the LLM literature agent? Who builds the BayBE integration? Who writes the MCP client? Who writes the plate reader parser? The PRD describes a system but doesn't break it into work streams. For a 24-hour hack with 3-5 people, ownership must be assigned before walking in the door.

---

## Minor Issues

- **Meeting quotes are overused.** They add flavor but make the PRD read more like a meeting summary than a product spec. Sections 2-3 could each lose 2-3 quotes and be tighter.
- **"Confirm with organizers" is still listed as ASAP.** The hack is March 14 and today is March 1. If not confirmed by now, "build cell-type-agnostic" should be the plan, not the fallback.
- **Post-Hackathon Transition section is premature.** The hack hasn't shipped yet. This reads like pitch deck padding. Focus the PRD on winning March 14-15.

---

## What's Strong

- Problem framing (Section 2) is excellent — clear problem, clear hypothesis, clear out-of-scope.
- Scoping decisions table says no to the right things.
- Demo Metrics (four numbers, one slide) is sharp.
- Hackathon targets table with Minimum/Strong/Stretch is well-calibrated.

---

## Bottom Line

The biggest risk is that the PRD describes a six-component architecture when what's needed is a three-component system that actually works: **(1) LLM generates recipes, (2) BayBE optimizes, (3) MCP executes.** Cut the world model, add a concrete fallback plan, fix the North Star metric, and add a work breakdown with owners. The difference between teams that win these hacks and teams that demo a slide deck is ruthless scope reduction.
