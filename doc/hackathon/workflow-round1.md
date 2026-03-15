# Workflow: Notion → Round 1 Pipetting Table

**Input:** Notion URL with hackathon details
**Output:** `SOT/experiments/round1-screening.md` (pipetting table ready for Monomer MCP)

---

## Stage 1: Extract Context

- **Tool:** Claude Code + browser (manual copy-paste from Notion; API/MCP extraction failed)
- **Input:** Notion URL (e.g. `https://monomer.notion.site/Format-...`)
- **Action:** Read the page, extract into structured markdown
- **Output:** 3 files:
  - `Track_A_Complete_Guide.md` — rules, reagents, workcell, labware
  - `pre-built-media.md` — 6 base media compositions with exact concentrations
  - `experimental-constraints.md` — hard limits: volumes, wells, time, precipitation, pipetting minimums

**Notes:**
- Notion client-rendered pages can't be fetched via WebFetch (returns JS bootstrap)
- Notion MCP only works for pages in your own workspace, not external shared pages
- In practice: user manually copied content from browser, Claude Code reformatted into markdown

## Stage 2: Design Search Space (Elnora Q1)

- **Tool:** Elnora CLI (`elnora tasks create`)
- **Input:** The 3 context files from Stage 1 (provided inline in prompt)
- **Action:** Ask **one question only**: "Which 3 components to optimize per media?"
- **Prompt includes:** all 6 media formulations, all 13 stocks, constraints, precipitation rules
- **Output:** Single Elnora response containing:
  - Top 3 components per media type (with biological rationale)
  - Concentration ranges (low/high spike with exact µL)
  - Base media volumes (128, 110, 130 µL)
  - Media suitability scoring (Semi-Defined 9.5, High Buffer 8.5, LBv2 6.5)

**Lesson learned:** We originally asked 4 questions (Q1-Q4: components, ranges, strategy, precipitation). Only Q1 was needed — it already contained ranges, volumes, and enough context. Q2-Q4 were wasted tokens.

## Stage 3: Generate DOE Table

- **Tool:** Claude Code (LLM computation — no Python DOE library used)
- **Input:** Elnora Q1 output + `experimental-constraints.md`
- **Action:**
  1. Select media types to test (3 from Q1 scoring)
  2. Calculate LHS points: divide each range into N bins, pick one value per bin, no repeats on any axis
  3. Convert concentrations to µL: `µL = (target / stock) × 200`
  4. Calculate water: `water = 180 - base - c1 - c2 - c3`
  5. Verify every row sums to exactly 180 µL
  6. Verify all volumes ≥ 5 µL (pipetting minimum)
  7. Verify all volumes are integers (Monomer API requirement)
- **Output:** Draft pipetting table (`doe-round1.md`)

**Rule: NEVER add components beyond Elnora Q1's recommendation.** Each media has exactly 3 optimization variables. If a problem arises (e.g. precipitation), solve it within those 3 variables or flag to the expert — do NOT invent a 4th component.

## Stage 4: Expert Review

- **Tool:** Human expert
- **Input:** Draft pipetting table
- **Action:** Expert reviews and makes final adjustments
- **Output:** Approved pipetting table

**What the expert changed in Round 1:**
- Kept original glucose values (rejected our cap from 9→5 g/L)
- Changed control from LBv2 to Novel Bio 180 µL
- No other modifications to SD or HB conditions

**This stage is intentionally manual.** The expert catches errors the agent can't (domain knowledge, lab intuition, practical constraints).

## Stage 5: Execute on Robot

- **Tool:** Monomer MCP (manual in Round 1 — not yet integrated with Claude Code)
- **Input:** Approved table from expert
- **Action:** Convert to transfer_array JSON format, submit to Monomer API
- **Output:** Experiment running on robot

## Stage 6: Record Source of Truth

- **Tool:** Claude Code
- **Input:** Actual experiment that ran (screenshot or Monomer MCP output)
- **Action:** Extract exact values into structured markdown
- **Output:** `SOT/experiments/round1-screening.md`

**Critical:** This file records what ACTUALLY ran, not what was planned. The doc may diverge from the plan due to expert review (Stage 4).

---

## Key Rules for the Agent

1. **One Elnora question, not four.** Q1 gives everything needed: components, ranges, volumes, scoring.
2. **3 components per media, no exceptions.** Never add a 4th component. If precipitation or other issues arise, flag to expert.
3. **Integer volumes only.** Monomer API rejects fractional µL.
4. **All volumes ≥ 5 µL.** Robot accuracy degrades below this.
5. **Every row = exactly 180 µL.** Plus 20 µL cells = 200 µL final.
6. **Expert review before robot.** Agent generates draft, expert approves.
7. **Record what actually ran.** SOT file must match reality, not the plan.
