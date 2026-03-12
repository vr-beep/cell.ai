# Track A Brief

**Track:** A — Media Optimization
**Cell type:** Vibrio natriegens (confirmed)
**Goal:** BUILD THE BEST MEDIA
**Competition:** 2 teams, head-to-head
**Track leads:** Carter Allen / Carmen Kivisild

---

## Core Requirement

Build an autonomous workflow that iteratively varies media components, runs cell culture, measures outcomes, and updates the next experiment end-to-end on REAL cells.

## Questions to Answer

The hackathon explicitly requires teams to address:

1. **What 3 media components are most impactful to optimize?** (from 16 available reagents)
2. **What dilution ranges for each component?**
3. **Is DOE (Design of Experiments) appropriate, or is Bayesian optimization better?**
4. **What media components cause precipitation, and is there a way to design against that?**

## Required Integrations

### 1. Monomer's MCP (Robot Control)
- Create media mixture
- Media exchange
- Incubate
- Plate read (OD600)

### 2. Elnora's MCP (Literature & Protocol Context)
- **Required.** "Integrate with Elnora's MCP to fully close the loop on deciding what media formulation to try next."
- **RESOLVED:** Elnora AI, Inc. (founded by Carmen Kivisild) is an independent SaaS agent for biomedical lab protocol generation. It is NOT an optimizer — it provides literature context, protocol drafting, and domain knowledge via 25 public MCP servers (PubMed, UniProt, KEGG, ChEMBL, etc.) under the **Augmented-Nature** GitHub org.
- **Elnora does NOT replace BayBE.** BayBE handles Bayesian experimental design; Elnora provides literature/protocol context. They are complementary.
- **Remaining:** Confirm exact MCP integration pattern for the hackathon with Carter Allen.

## Phase 1 Research Deliverables (12PM-2PM)

Before Phase 2 Build starts, we must have:

- [ ] Which 3 of 16 reagents to optimize
- [ ] Dilution ranges for each
- [ ] Precipitation avoidance rules (hard constraints)
- [ ] DOE vs. Bayesian optimization decision
- [ ] Understanding of Elnora's MCP capabilities
- [ ] Familiarity with Monomer's MCP from tutorial

## Tutorial (1 hour, 12-1PM)

Monomer staff walks Track A teams through a seeding density experiment on the workcell. This is our hands-on MCP learning time. Use it to:

- Understand MCP command format and response structure
- See plate reader output format (CSV? JSON?)
- Learn the plate → incubator → reader workflow
- Identify any gotchas (latency, state requirements, error handling)

## Strategic Notes

- **Elnora does NOT replace BayBE.** Elnora is a literature/protocol agent; BayBE is the optimization engine. We need both: BayBE decides *which* experiment to run, Elnora helps with *how* to run it and provides domain context.
- **Robots sleep at midnight.** Cap experimental rounds at ~6 maximum.
- **V. natriegens advantage:** ~10 min doubling time = ~45 min incubation rounds. More iterations than any mammalian cell team.
- **LBv2** is the basal media (shown in Monomer's Culture Monitor). Use as baseline control.
