# Crafting Effective Elnora Prompts

Elnora works best when treated like a new, highly knowledgeable postdoc joining your lab. Don't just say *what* — give biological context, constraints, and prior results.

## Step 0: Read ALL Source Documents FIRST

**Before writing a single word of the prompt, read EVERY file the user points you to.** Not some. ALL. This includes CSVs, databases, guides, recipes — everything.

Why: Partial reads cause you to:
- Misclassify things (calling prepared media "reference recipes")
- Miss entire categories of information (ignoring reagent databases)
- Invent structure that doesn't match reality (one generic answer when per-item answers are needed)

**Checklist before drafting:**
- [ ] Read every file in the source directory
- [ ] Identify what is **physical inventory** (things on the shelf) vs **reference info** (background knowledge)
- [ ] Note the structure: how many items? Are they independent? Does each need its own answer?

## Step 1: Required Elements

Every prompt to Elnora MUST include all four:

| Element | What to provide | Example |
|---------|----------------|---------|
| **Biological context** | Exact organism, strain, cell line | *V. natriegens*, CHO-K1 suspension, WTC-11 iPSCs |
| **Current state & baseline** | Current media, prior results, failure points | "OD600 maxes out at 0.8 in LB + 1.5% NaCl" |
| **Lab constraints** | Equipment, format, volumes, automation, **full inventory** | 96-well plates, robotic workcell, 1 mL volume, **all stocks with concentrations** |
| **Output format** | What deliverable you need | Step-by-step protocol, DOE matrix, plate layout, master mix table |

## Step 2: Iron Rule — Never Guess Missing Elements

If any element is unknown — **ASK the user, do not fill it in with assumptions**. A gap dressed up as a fact is a hallucination.

- Do NOT infer baseline from available documents unless the user confirms it
- Do NOT pick a "likely" value — if there are multiple options, present them and ask
- If there is no baseline, say "no baseline data yet" explicitly
- Mark unknown elements with `[UNKNOWN — ask user]` in the draft

## Step 3: Match Output to Input Structure

**The output format must reflect the structure of the input.** If the user has 6 media, the answer should address each of the 6 — not collapse into one generic list.

Ask yourself:
- How many distinct items does the user have? (6 media → 6 answers)
- Are they interchangeable or different? (different compositions → different recommendations)
- Does a single answer make sense, or does each item need its own?

## Step 4: Use Precise Language

Elnora doesn't know your lab. Call things what they are:

| Wrong | Right | Why |
|-------|-------|-----|
| "Reference recipes" | "Prepared media available in the lab" | Elnora needs to know these are physical products, not literature |
| "We have LBv2, Defined Minimal..." | Full compositions with concentrations | Names mean nothing to Elnora |
| "Available stocks" without a list | Full table: reagent + stock concentration | Elnora can't recommend what it doesn't know exists |

## Prompt Template

```
[Biological context]: organism, strain, growth phase
[Current state]: baseline media or "first experiment, no baseline"
[Physical inventory - prepared media]: full compositions of each
[Physical inventory - reagent stocks]: full table with concentrations
[Lab constraints]: equipment, plate format, volumes
[Special constraints]: precipitation rules, compatibility warnings
[Goal]: what you want to optimize or achieve
[Output format]: matched to input structure (per-media? per-component? single list?)
```

## Red Flags — Fix Before Sending

| Problem | Example | Fix |
|---------|---------|-----|
| Didn't read all source files | Skipped the CSV reagent database | Go back and read everything |
| Guessed baseline | Picked LBv2 because file says "Prepared" | Ask the user |
| Generic output for structured input | "Top 3 components" when there are 6 different media | Ask per-media |
| Names without compositions | "We have Semi-Defined Media" | Include full composition |
| Missing inventory | Listed stocks from memory, missed actual database | Use the real source file |
| Confused reference vs physical | Called prepared media "reference recipes" | Clarify what's on the shelf vs what's background info |

## Step 5: Always Include Replicates and Blanks in Design Requests

When asking Elnora for plate layouts or experimental designs, **always specify replicates and blanks** as part of the constraints. Without them, data is statistically unreliable and OD600 readings cannot be blank-corrected.

- Minimum: 3 replicates + 1 blank per condition (4 wells per condition)
- Tell Elnora the total well budget including replicates, not just the number of conditions
- Example: "8 conditions × 4 wells each = 32 wells, plus 8 wells for controls = 40 total"

**Lesson learned:** A plan with 8 unique conditions in 8 wells (no replicates, no blanks) produces unreliable data. The real experiment used 10 conditions × 4 wells = 40 wells.

## Step 6: Account for Base Media Dilution

When the base media volume is less than ~80% of total well volume, components "already at saturating levels" may no longer be saturating. Always calculate the **effective final concentration** after dilution.

Example: Semi-Defined has 5 g/L Tryptone. At 130 µL base in 200 µL total, effective Tryptone = 5 × (130/200) = 3.25 g/L — no longer saturating, worth optimizing.

**Lesson learned:** We dismissed Tryptone/YE as "already saturating" without calculating dilution. The real experiment varied both successfully.

## Power Moves

- **Share failed experiments** — negative data is Elnora's most valuable input
- **Ask for calculations** — exact volumes in uL from stock solutions, seeding densities, surface area math
- **Request plate layouts** — Elnora generates ready-to-execute well maps
- **Iterate in conversation** — refine via `tasks send`, don't restart tasks
- **Attach files** — use `--file-refs` to give Elnora your data (CSV, prior protocols)
- **Ask for dilution math** — when base media < 80% of total volume, ask Elnora to recalculate effective concentrations
