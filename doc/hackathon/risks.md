# Key Risks & Uncertainties — Track A Hackathon

Based on `context.md` and `../artifacts/PRD-media-optimization-agent.md`.

---

## Critical Risks (could block us entirely)

### 1. ~~Elnora is a black box~~ RESOLVED
- **Elnora AI, Inc.** is an independent SaaS product (founded by Carmen Kivisild, Salt Lake City) — NOT a Monomer product.
- It's an autonomous AI agent for biomedical lab protocol generation and optimization (Connect → Think → Execute pipeline).
- Its GitHub org (**Augmented-Nature**) maintains **25 public MCP server repos** covering life sciences databases (PubMed, UniProt, AlphaFold, ChEMBL, KEGG, Ensembl, etc.).
- **Elnora does NOT replace BayBE.** Elnora does *protocol-level* optimization (reagent concentrations, step ordering, literature context). BayBE does *Bayesian experimental design* (mathematically selecting the next experiment from a combinatorial space). They are complementary.
- **Architecture decision:** Keep BayBE for optimization. Use Elnora + its MCP servers as a literature/context/protocol layer.
- **Remaining unknown:** Exact MCP integration pattern for the hackathon (how Elnora expects to receive experimental results).

### 2. Monomer MCP schema unknown
- We know the 4 actions (create media, media exchange, incubate, plate read) but not the exact API shape — request/response format, parameter names, error codes
- Tutorial is only 1 hour and shared with the competing team
- **Impact:** Integration bugs could eat hours of Phase 2
- **Mitigation:** Use tutorial time efficiently. Have someone take detailed notes on every MCP call. Ask for API docs or example payloads in advance.

### 3. Stock concentrations unknown until day-of
- Dilution ranges depend on stock concentrations from Monomer's reagent labels
- Can't finalize search space parameters in advance
- **Impact:** Phase 1 research hour is even more compressed
- **Mitigation:** Pre-compute ranges parametrically (e.g., "if stock is X mM, range is Y-Z"). Have a spreadsheet ready to plug in values.

---

## High Risks (likely to cause significant problems)

### 4. Time budget is brutally tight
- 2:00 PM start to 12:00 AM robot cutoff = **10 hours** of execution time
- ~45 min per round = **~6 rounds max** (optimistic — assumes zero debugging time)
- First round will be slowest (integration issues, pipeline bugs)
- **Impact:** Realistically 3-4 usable optimization rounds. May not converge.
- **Mitigation:** Design round 1 to also be a valid experiment (not a throwaway test). Parallelize well conditions within each round to maximize data per round.

### 5. Precipitation kills wells silently
- 3 known precipitation constraints, possibly more unknown ones
- A precipitated well wastes a slot and produces misleading OD600 (turbidity != growth)
- **Impact:** Bad data fed back into optimizer -> cascading bad suggestions
- **Mitigation:** Encode hard constraints in search space. Include a control well per plate. Consider OD600 sanity checks (e.g., flag suspiciously high T=0 readings as precipitation).

### 6. OD600 is a noisy proxy
- Absorbance measures turbidity, not live cell count directly
- Dead cells, debris, and precipitates all contribute to OD600
- With only ~45 min incubation, signal-to-noise ratio may be low
- **Impact:** Optimizer may chase noise rather than real growth differences
- **Mitigation:** Use replicates (multiple wells per condition). Include LBv2 control to anchor readings. Consider growth rate (delta-OD) rather than absolute OD.

---

## Medium Risks (manageable but worth tracking)

### 7. Choosing the wrong 3 components
- We're pre-selecting 3 of 16 reagents based on literature + intuition
- If our picks are wrong (e.g., Tryptone/Yeast Extract are already in LBv2 and the real leverage is elsewhere), all rounds are wasted on a flat optimization landscape
- **Mitigation:** Validate picks during Phase 1 with scientist input. Consider a broader initial screen in round 1.

### 8. Robot reliability / queue contention
- Two teams share Track A infrastructure (or at minimum, the same facility)
- Robot errors (failed transfers, arm collisions, plate jams) are real
- **Impact:** Lost rounds, corrupted plates
- **Mitigation:** Understand error handling in MCP. Build retry logic. Clarify day-of whether teams share hardware or have dedicated workcells.

### 9. Dashboard / demo readiness
- Judges evaluate at 4:30 PM Sunday. We need a compelling visual story, not just raw data.
- Building the dashboard competes for the same time as running experiments
- **Impact:** Great science but poor demo -> lose to a team with a slicker presentation
- **Mitigation:** Start dashboard skeleton early (pre-hackathon if possible). Have one person own demo prep while others run experiments.

---

## Uncertainties (unknowns that could go either way)

| Uncertainty | Optimistic case | Pessimistic case |
|---|---|---|
| ~~Elnora capabilities~~ | ~~Full experiment design engine — we just orchestrate~~ | ~~Thin wrapper — we must bring our own optimizer~~ RESOLVED: Elnora is a literature/protocol agent, not an optimizer. BayBE handles optimization. |
| Plate reader output format | Clean JSON via MCP | Raw CSV requiring parsing |
| Fluorescence availability | Extra readout channel for richer data | Not available — OD600 only |
| Team composition | Domain scientist on team to guide choices | Pure software team — biology blind spots |
| Competing team's approach | Different strategy — we both learn | Same approach but better execution — pure speed race |
| LBv2 composition | Published / shared during tutorial | Proprietary — we optimize blind to baseline |

---

## Pre-hackathon Actions to Reduce Risk

1. ~~**Email Carter/Carmen:** Ask about Elnora (what it does, API docs)~~ DONE — Elnora researched. Still need MCP schema and workcell sharing info from Carter/Carmen.
2. **Build BayBE as primary optimizer:** Elnora confirmed as literature/protocol layer, not an optimizer. BayBE is the primary optimization engine, not a fallback.
3. **Pre-compute reagent ranges:** Parametric spreadsheet for stock concentration to search range conversion
4. **Dashboard skeleton:** Basic Streamlit/panel layout ready to plug in live data
5. **Precipitation constraint engine:** Hard constraints codified and tested before day-of
