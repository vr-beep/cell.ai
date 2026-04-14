# Papers KB — Lessons for Cell.ai Media Optimization

_Generated 2026-04-14. Companion to `literature-review.md` (Elnora-sourced). This file captures critically-filtered, actionable lessons from 3 externally-supplied papers, with caveats._

**Sources:**
1. **Narayanan et al.** — "Accelerating cell culture media development using Bayesian optimization-based iterative experimental design" — _Nat Commun_ 16:6055 (2025). DOI: 10.1038/s41467-025-61113-5. Code: `github.com/NHarini-1995/CellCultureBayesianOptimization`
2. **Gupta et al.** — "LLMs for Bayesian Optimization in Scientific Domains: Are We There Yet?" — _EMNLP Findings_ 2025, pp. 15482–15510.
3. **Wei et al.** — "Outpacing E. coli: Development of V. natriegens as a Next-Generation Cloning Host" — bioRxiv 2026.02.11.705132 (preprint, not peer-reviewed).

---

## Paper 1 — Narayanan et al. (BO for media optimization)

### L1.1 — Use LHS for the seed round
- **Lesson:** Space-filling Latin Hypercube Sampling for the initial batch gives the GP a balanced first view of the design space and outperforms random/grid initialization.
- **Evidence:** Methods "Initial design" section + Fig. 4B showing broad initial coverage.
- **Caveat:** Generally established technique; not paper-specific. Paper uses LHS with ~24 initial points in 8D; our 3D space needs fewer.
- **Action:** Verify BayBE seed strategy is LHS or Sobol, not uniform random. Target ~14 seed conditions for our plate layout.

### L1.2 — GP kernel = Matérn 5/2 with ARD
- **Lesson:** Matérn 5/2 kernel with automatic relevance determination (per-dimension lengthscales) is their default and performs well across both case studies.
- **Evidence:** Methods "Gaussian processes" section, Eq. 2.
- **Caveat:** Single ablation-free choice; no comparison with RBF or Matérn 3/2 in paper.
- **Action:** Check BayBE's default kernel; set to Matérn 5/2 + ARD explicitly.

### L1.3 — Schedule explore → exploit across rounds
- **Lesson:** Their BO naturally shifts from broad exploration (iter 0–2) to exploitation (iter 3+), measured by decreasing spread in design space.
- **Evidence:** Fig. 5A–C (clear visualization of narrowing search over iterations).
- **Caveat:** They had 6–7 iterations to work with; we have 2–3. The natural schedule may not emerge — we may need to force it via acquisition function β.
- **Action:** Configure BayBE with higher exploration (high UCB β or pure Sobol) for seed+round 1, lower β for round 2+.

### L1.4 — Transfer learning for adding factors mid-campaign
- **Lesson:** When new factors are introduced in a later round, prior data can seed the new GP — reducing experiments vs. restart from zero.
- **Evidence:** Fig. 6 (HSA productivity, BO-TL ~160 exp vs full screen ~4864).
- **Caveat:** Single case study; magnitude of saving not independently replicated.
- **Action:** Persist round data in a format that can be re-ingested if we expand the search space (e.g., add Tryptone or pH as a 4th factor in round 2+).

### L1.5 — Constrained-objective pattern
- **Lesson:** Soft-penalty objective combining a primary target with viability/constraint floor (Eq. 7).
- **Evidence:** Methods "Bayesian optimization" section.
- **Caveat:** Specific to their PBMC viability+distribution target; not directly our growth-rate objective.
- **Action:** Reference if we add a constraint later (e.g., OD600_min floor before optimizing specific growth).

### L1 Global caveats
- Their budget was 72–90 experiments. Our budget is ~30–45. Algorithm behavior at our scale is **untested**.
- Claimed "3–30× fewer experiments" is vs. full-factorial screens, not well-designed DoE. True reduction vs. BBD/CCD is ~1.4–3.4×.
- Convergence not proven — they stopped iterating, not reached optimum.

---

## Paper 2 — Gupta et al. (LLMs for BO)

### L2.1 — LLMs ignore in-context experimental feedback
- **Lesson:** When researchers randomized the feedback labels fed to LLM-based agents (BDA-Rand), performance was unchanged. The LLM relies on pretraining priors, not the current experimental history.
- **Evidence:** Table 1 (BDA vs BDA-Rand on 5 gene datasets, across Llama/Qwen/Claude 3.5 backbones).
- **Caveat:** Tested on discrete candidate selection (pick genes from 19k), not continuous media optimization. Conclusion may over-generalize.
- **Action:** Do not let Elnora or any LLM choose the next media composition based on previous-round results. BayBE is the optimizer.

### L2.2 — Classical GP/UCB beats LLM-as-optimizer
- **Lesson:** Using the SAME LLM embeddings to condition a Linear UCB or GP outperforms the LLM-agent framework that ostensibly uses those embeddings plus reasoning.
- **Evidence:** Table 2 (LinearUCB and GP beat BDA on both Llama and Qwen backbones on most datasets).
- **Caveat:** Discrete candidate setting; continuous BO may differ.
- **Action:** Keep BayBE (GP-based) as the selection engine. LLMs do not add value to the loop itself.

### L2.3 — LLMNN pattern: LLM for seeds, classical for expansion
- **Lesson:** Hybrid approach — ask LLM once to propose cluster-center candidates (priors), then NN-expand in embedding space for the batch — beats both pure-LLM and pure-classical methods.
- **Evidence:** Table 3 (LLMNN beats BDA-GS and classical baselines on most gene datasets).
- **Caveat:** Still discrete candidate selection. For continuous variables, "nearest neighbour in embedding space" is not directly translatable.
- **Action:** Use Elnora to propose seed media compositions informed by literature (1–3 expert conditions). Add them to the BayBE initial LHS batch. Do not use Elnora beyond seed round.

### L2 Global caveats
- Tested on Claude 3.5 Sonnet, Llama-3.1-8B, Qwen-2-7B. Frontier models (Claude Opus, GPT-4) not tested — may behave differently.
- Task is discrete candidate selection from large pools (19k genes, ~1k molecules). Our task is 3D continuous variable tuning.
- Primary takeaway is defensive (what NOT to do), not prescriptive.

### L2 Primary takeaway
**Elnora's role in our loop:** literature context, seed suggestions, result interpretation, protocol text generation. **Never** closing the loop on "pick the next media."

---

## Paper 3 — Wei et al. (V. natriegens CyClone)

### L3.1 — pH drifts UP in rich V. natriegens media
- **Lesson:** During growth on rich media (tryptone/YE), pH increases significantly due to ammonia release from amino-acid catabolism.
- **Evidence:** Results "Media development" section.
- **Caveat:** Qualitative, no timecourse data shown; observed in CyClone which differs from wild-type.
- **Action:** Validates our MOPS pH 7 buffering choice. Consider monitoring final-culture pH in at least one condition per round as a sanity check.

### L3.2 — V. natriegens is peroxide-sensitive in autoclaved media
- **Lesson:** Peroxides generated during autoclaving are toxic to V. natriegens; CyClone adds an extra oxyR-C208G copy to compensate (+60–80% plasmid yield).
- **Evidence:** Results "Stress response genes" section, Fig. 3–4.
- **Caveat:** Effect is strain-specific (CyClone has extra oxidative defense); wild-type behavior may vary. This is a known V. natriegens property, not novel to this paper.
- **Action:** Ask Monomer Bio how media is sterilized. If autoclaved and strain is wild-type, peroxide sensitivity could contribute to lag/variability. Rule out before attributing to media composition.

### L3.3 — Marine ions matter beyond NaCl
- **Lesson:** V. natriegens is a marine organism; MgSO₄ and K₂HPO₄ are part of optimized media, not just NaCl.
- **Evidence:** Results "Media development" section (ions mentioned as "most abundant marine ions").
- **Caveat:** Exact concentrations in supplementary (not read). This is general V. natriegens biology — LBv2 recipe already includes MgCl₂ + KCl.
- **Action:** Confirm Monomer's base media contains MgSO₄/MgCl₂ and a phosphate source. If absent, our NaCl-glucose-YE optimum may be partially compensating for missing marine ions.

### L3.4 — LBv2 as baseline reference
- **Lesson:** LBv2 (LB Miller + MgCl₂ + KCl + extra NaCl) is the widely-used wild-type V. natriegens reference medium.
- **Evidence:** Paper introduction to media section, cites prior literature.
- **Caveat:** Rich/undefined; not a BO target. Useful only as positive control.
- **Action:** If plate layout allows, include one LBv2 well per round as a positive control reference.

### L3 Global caveats
- bioRxiv preprint, not peer-reviewed. Commercial product pitch (NBx CyClone™).
- CyClone has 5+ genetic modifications (Δdns, ΔrecA, Δϕpro1/2, dns::oxyR2, mltG::spec). **Results do not directly transfer to wild-type V. natriegens.**
- Their optimization target was plasmid DNA yield at 6h, not growth rate. The media optimum for plasmids ≠ optimum for growth (metabolic burden tradeoff).

---

## Related literature (already in `literature-review.md`)

Cross-reference rather than duplicate:
- **Forsten et al. 2024** (DOI 10.1186/s12896-024-00897-8) — defined medium; NaCl 7.5–15 g/L, MOPS 180–300 mM, μ=1.97 ± 0.13 h⁻¹. **Most directly comparable to our setup.**
- **Biener et al. 2023** (DOI 10.1007/s00253-023-12799-4) — low-chloride defined medium, NaCl replaced by Na₂HPO₄/Na₂SO₄/citrate; bioreactor scale.
- **Hädrich et al. 2025** (DOI 10.1186/s12934-025-02693-1) — minimal medium + glucose + acetate maintenance feed; μ=1.16 ± 0.03 h⁻¹.

---

## Cross-cutting warnings — apply regardless of paper

1. **Budget mismatch.** Papers operated at 72–640 experiments. We have ~30–45. None of them validate BO at our scale. Real risk: BO underperforms Sobol/random at very low iteration counts. Mitigation: run a simulation/sanity check before committing to BO.

2. **Dimensionality mismatch.** Our problem is 3 continuous variables. Papers operate on 5–8+ dimensions or large discrete candidate pools. For 3D continuous, a well-chosen Sobol sequence (~30 points) followed by post-hoc GP fitting may match or beat iterative BO. Honest question: do we even need closed-loop BO for 3 variables?

3. **Objective mismatch.** OD600-derived specific growth rate has multiplicative/log-normal noise (exponential growth + measurement noise). Papers optimize viability (% scale, bounded) or hits (discrete). **Consider log-transforming growth rate before GP fitting.** None of the three papers address this.

4. **Strain/context mismatch.** CyClone ≠ wild-type. Paper 1's PBMC/K. phaffii ≠ V. natriegens. Published media optima do not transfer without validation. Confirm Monomer's exact strain and base media before assuming any literature recipe is a good prior.

---

## Open questions to resolve before hackathon

1. What is the exact V. natriegens strain Monomer Bio is providing (wild-type, ATCC number)?
2. What is the base media composition Monomer prepares — does it include MgSO₄/MgCl₂, K₂HPO₄, or only tryptone/YE/NaCl/MOPS?
3. How is the media sterilized (autoclave vs filter-sterilized)? Autoclaving introduces peroxide exposure.
4. Should OD600-derived growth rates be log-transformed before BayBE ingests them?
5. What is Elnora's precise role in the closed-loop pipeline? Audit to ensure it never picks the next condition (Paper 2 warning).
6. Is BayBE configured with LHS seed strategy and Matérn 5/2 + ARD kernel (Paper 1 defaults)?
