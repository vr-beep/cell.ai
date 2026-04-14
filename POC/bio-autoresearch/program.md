# bio-autoresearch

Autonomous media optimization for V. natriegens growth, inspired by Karpathy's autoresearch.

## Setup

1. **Agree on a run tag** and create branch: `git checkout -b bio-autoresearch/<tag>`
2. **Read the in-scope files**:
   - `simulator.py` — fixed GP surrogate trained on real wet-lab data. DO NOT MODIFY.
   - `recipe.py` — the file you modify. Media recipes and search strategy.
   - `program.md` — these instructions.
3. **Initialize results.tsv** with header row.
4. **Run baseline**: `python recipe.py` as-is to establish baseline growth rate.

## The Problem

We are optimizing cell culture media for *Vibrio natriegens*, the fastest-growing non-pathogenic bacterium (~10 min doubling time). The goal is to find the media composition that maximizes growth rate (h⁻¹).

**Search space (3 variables, g/L):**
- NaCl: 10–35 g/L (V. natriegens is a marine halophile, needs salt)
- Glucose: 1–20 g/L (carbon source)
- Yeast Extract: 2–10 g/L (complex nitrogen/vitamin source)

**Fixed:** Tryptone 10 g/L, MOPS pH 7.

**Baseline:** NaCl=10, Glucose=1, YE=5. Published max growth rate: ~4.4 h⁻¹.

## Experimentation

Each experiment runs `python recipe.py` which evaluates your recipes against the GP surrogate (trained on real Round 1-3 data from the Monomer Bio robotic workcell).

**What you CAN do:**
- Modify `recipe.py` — change the `generate_recipes()` function. Try different strategies: grid search, random search, Bayesian-inspired, biological reasoning, gradient-free optimization, etc.
- Use `query_elnora()` to ask Elnora AI real scientific questions about V. natriegens biology, optimal media, known interactions. Elnora searches PubMed, ArXiv, and scientific databases. Use this to form literature-backed hypotheses before designing recipes.

**What you CANNOT do:**
- Modify `simulator.py`. It is read-only.
- Install new packages. Use only stdlib + numpy.

**The goal: get the highest best_growth_rate.**

**Simplicity criterion**: simpler strategies that achieve similar results are preferred.

## Output format

The script prints:
```
---
n_recipes:        10
best_growth_rate: 2.3456
best_recipe:      {"nacl_g_l": 20.0, "glucose_g_l": 10.0, "yeast_extract_g_l": 7.0}
```

## Logging results

Log each experiment to `results.tsv` (tab-separated):

```
commit	best_rate	n_recipes	status	description
```

Example:
```
a1b2c3d	1.8500	10	keep	baseline grid
b2c3d4e	2.1200	14	keep	focused search around NaCl=20 region
c3d4e5f	1.9000	10	discard	random sampling (worse than current best)
```

## The experiment loop

LOOP FOREVER:

1. Look at results so far — what worked, what didn't?
2. Form a hypothesis about what media composition might work better. Think like a scientist:
   - Does V. natriegens prefer high or low salt? (it's a marine organism)
   - Is glucose helping or inhibiting? (catabolite repression is real)
   - What's the interaction between YE and glucose?
3. Modify `generate_recipes()` in `recipe.py` with your new strategy.
4. `git commit`
5. Run: `python recipe.py > run.log 2>&1`
6. Read results: `grep "^best_growth_rate:" run.log`
7. Log to results.tsv
8. If best_growth_rate improved → keep (advance branch)
9. If worse → `git reset --hard HEAD~1` (discard)
10. GOTO 1

**NEVER STOP.** You are an autonomous researcher. If you run out of ideas, think harder — consider biological interactions, published literature on V. natriegens optimal media, systematic exploration of undersampled regions.
