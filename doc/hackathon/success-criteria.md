# Track A Success Criteria: AI Agent for Media Composition Optimization

**Purpose:** Judging reference for the 24hr AI Science Cell Culture Hack @ Monomer Bio
**Track:** A — Closed-Loop Media Optimization
**Date:** March 14-15, 2026

---

## 1. Closed-Loop Autonomy (Highest Weight)

**Core question:** Did the loop actually close?

- Agent designs composition -> robot mixes -> incubates -> reads OD600 -> agent learns -> proposes next round — with zero human intervention
- Number of fully autonomous rounds completed (2 = minimum, 5-6 = exceptional)
- This is the literal track requirement: *"iteratively varies media components, runs cell culture, measures outcomes, and updates the next experiment end-to-end"*

**What separates good from great:** A team that ran 2 clean rounds beats a team that ran 5 broken rounds with manual patching.

---

## 2. Measurable Biological Outcome (High Weight)

**Core question:** Did the AI actually find better media?

- Best growth rate achieved vs. basal media control (LBv2)
- Round-over-round improvement — did the agent *learn*, not just *run*?
- Approaching the published V. natriegens max growth rate (~10 min doubling) is the gold standard
- A self-referencing metric ("we improved 50% from our own bad start") is easily gamed — judges will look for comparison against an independent baseline

| Metric | Minimum | Strong | Stretch |
|---|---|---|---|
| Best growth rate vs. basal control | Any measurable gain | >30% above basal | >2x basal |
| Rounds completed autonomously | 2 | 5 | 6 (robots sleep at midnight) |
| Rounds to beat baseline | <=3 | 2 | 1 (LLM alone wins) |
| Human interventions per loop | 0 | 0 | 0 |

---

## 3. Integration Quality (High Weight)

**Core question:** Did you actually use the required tools?

- Integration with **Elnora's MCP** (experiment design) — required, not optional
- Integration with **Monomer's MCP** (robotic execution) — all four actions:
  - Create media mixture
  - Media exchange
  - Incubate
  - Plate read (OD600)
- Seamless orchestration between the two MCPs
- Teams that skip Elnora or do manual workarounds will be penalized

---

## 4. Scientific Rigor (Medium Weight)

**Core question:** Did you make smart experimental choices?

- Thoughtful selection of 3 components to optimize (from 16 available) with clear rationale
- Appropriate dilution ranges grounded in literature/domain knowledge
- Precipitation constraints properly handled:
  - CaCl2 + phosphate -> calcium phosphate (insoluble)
  - FeCl3 + high pH -> iron hydroxide
  - High MgSO4 + high pH -> magnesium hydroxide
- Proper controls (basal media wells on each plate)
- Fresh plates per round to avoid carryover confounding
- Replicates for statistical confidence

---

## 5. AI/Optimization Sophistication (Medium Weight)

**Core question:** Was the AI approach smart, not just mechanical?

- Literature-informed priors (not random starting guesses)
- Bayesian optimization or equivalent that balances explore vs. exploit
- Evidence that the optimizer *converged* — narrowing variance across rounds
- Smart handling of limited rounds (~6 max) — every round counts

---

## 6. Demo and Storytelling (Medium Weight)

**Core question:** Can you explain what happened and why it matters?

- Clear visualization of the optimization journey (dashboard, charts)
- The "one slide, four numbers" pitch:
  1. **Best growth rate vs. basal** — "Our AI's best recipe outperformed basal media by X%"
  2. **Growth rate improvement** — "Cell growth rate improved Y% from round 1 to round N"
  3. **Rounds completed autonomously** — "Our agent ran N closed loops with zero human intervention"
  4. **Compositions explored** — "The system designed, executed, and learned from Z unique media recipes in 24 hours"
- Compelling narrative: "AI found something a human couldn't in this timeframe"

---

## 7. Robustness and Error Handling (Lower Weight)

- Graceful handling of MCP failures, retries, unexpected plate reader output
- Agent didn't crash mid-loop
- Recovery from transient errors without human intervention

---

## What Wins

The winning team shows **3+ fully autonomous rounds with clear growth improvement over basal media, tight Elnora + Monomer MCP integration, and a crisp demo that tells the learning story with real data from real cells.**

Judges care about the loop closing cleanly and the biology actually working — not fancy dashboards or theoretical architecture.

---

## Weight Summary

| Criterion | Weight |
|---|---|
| Closed-loop autonomy | Highest |
| Measurable biological outcome | High |
| Integration quality (Elnora + Monomer MCPs) | High |
| Scientific rigor | Medium |
| AI/optimization sophistication | Medium |
| Demo and storytelling | Medium |
| Robustness and error handling | Lower |
