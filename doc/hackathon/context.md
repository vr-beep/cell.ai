# Hackathon Context — Track A: Media Optimization

> Single-source reference for the 24hr AI Science Cell Culture Hack.
> Consolidates format, hardware, reagents, and Track A brief.

---

## 1. Event Overview

- **Event:** 24hr AI Science Cell Culture Hack @ Monomer Bio (5th in series)
- **Dates:** March 14-15, 2026
- **Location:** Monomer Bio HQ, San Francisco
- **Competition:** 3 tracks total, 2 teams per track. Head-to-head on Track A.
- **Track leads:** Carter Allen / Carmen Kivisild

### Schedule

#### Saturday, March 14

| Time | Activity |
|---|---|
| 9:30 AM | Check-in + breakfast |
| 10:00 AM | Kickoff |
| 11:00 AM | Finalize teams |
| 12:00-1:00 PM | **Phase 1 Tutorial:** Monomer staff walks through a seeding density experiment on the workcell |
| 1:00-2:00 PM | **Phase 1 Research:** Answer key research questions (see Section 5) |
| 2:00 PM | **Phase 2: Build** begins |
| 6:00 PM | Dinner + round table talks |
| 7:00 PM | Hack + build continues |
| 12:00 AM | **Robots go to sleep** — no more experimental runs after midnight |

#### Sunday, March 15

| Time | Activity |
|---|---|
| Overnight | Analysis, dashboard, demo prep |
| 3:00 PM | Final submission deadline |
| 3:30-4:30 PM | Walk-around showcase |
| 4:30-5:30 PM | Demos + pitching |

---

## 2. Track A Brief

- **Track:** A — Media Optimization
- **Cell type:** Vibrio natriegens
- **Goal:** BUILD THE BEST MEDIA
- **Approach:** Build an autonomous workflow that iteratively varies media components, runs cell culture on REAL cells, measures outcomes (OD600), and updates the next experiment — end-to-end.

### Required Integrations

1. **Monomer's MCP (Robot Control)** — create media mixture, media exchange, incubate, plate read (OD600)
2. **Elnora's MCP (Literature & Protocol Context)** — required integration for domain knowledge and protocol generation

> **RESOLVED:** Elnora AI, Inc. (founded by Carmen Kivisild) is an independent SaaS agent for biomedical lab protocol generation. Its GitHub org (Augmented-Nature) maintains 25 public MCP servers for life sciences databases. Elnora does NOT replace BayBE — it provides literature/protocol context, not Bayesian optimization.

### Strategic Notes

- **Elnora does NOT replace BayBE.** Elnora is a literature/protocol agent; BayBE is the optimization engine. They are complementary — BayBE decides *which* experiment to run, Elnora provides domain context and protocol drafting.
- **V. natriegens advantage:** ~10 min doubling time = ~45 min incubation rounds. More iterations than any mammalian cell team.
- **LBv2** is the basal media (shown in Monomer's Culture Monitor). Use as baseline control.

---

## 3. Hardware & MCP Actions

### Robotic Workcell

| Equipment | Description |
|---|---|
| **Opentrons Flex** | Liquid handler — mixes media, performs media exchanges |
| **Liconic LPX-220 Carousel** | Plate storage carousel |
| **Liconic STX-110** | 4C incubator (cold storage for prepared plates/reagents) |
| **Liconic STX-220** | 37C incubator (growth incubation — V. natriegens grows at 37C) |
| **Tecan Infinite** | Plate reader — OD600 absorbance readout |
| **KX-2 Robotic Arm** | Moves plates between instruments |

### MCP Actions

| Action | Description |
|---|---|
| **Create media mixture** | Robot mixes specified composition using Opentrons Flex |
| **Media exchange** | Robot applies new media to wells |
| **Incubate** | Robot moves plate to STX-220 for specified time. Temperature controllable via MCP (default 37C for V. natriegens). |
| **Plate read** | Robot reads OD600 via Tecan Infinite plate reader |

### Readout Notes

- No microscope — OD600 (absorbance) is the primary readout
- Fluorescence may also be available via Tecan Infinite (confirm day-of)

---

## 4. Reagent Database (16 reagents)

**Basal media:** LBv2 (baseline control)

| # | Reagent | Category | Notes |
|---|---|---|---|
| 1 | Tryptone | Nitrogen source | Primary protein source in LB media |
| 2 | Yeast Extract | Nitrogen source | Vitamins, amino acids, growth factors |
| 3 | Sodium Chloride (NaCl) | Salt | Required for V. natriegens (marine halophile). Hard requirement. |
| 4 | Glucose | Carbon source | Primary carbon/energy source |
| 5 | Glycerol | Carbon source | Alternative carbon source |
| 6 | Magnesium Sulfate (MgSO4) | Trace metal/cofactor | Essential cofactor for many enzymes |
| 7 | Calcium Chloride (CaCl2) | Trace metal | Cell signaling, membrane stability |
| 8 | Potassium Phosphate Monobasic (KH2PO4) | Buffer/phosphate | Buffering + phosphate source |
| 9 | Potassium Phosphate Dibasic (K2HPO4) | Buffer/phosphate | Buffering + phosphate source |
| 10 | Ammonium Chloride (NH4Cl) | Nitrogen source | Inorganic nitrogen |
| 11 | Sodium Hydroxide (NaOH) | pH adjuster | Raises pH |
| 12 | Hydrochloric Acid (HCl) | pH adjuster | Lowers pH |
| 13 | Iron(III) Chloride (FeCl3) | Trace metal | Essential trace element |
| 14 | Manganese Sulfate (MnSO4) | Trace metal | Essential trace element |
| 15 | Zinc Sulfate (ZnSO4) | Trace metal | Essential trace element |
| 16 | Thiamine (Vitamin B1) | Vitamin | Growth factor |

*Exact stock concentrations to be confirmed day-of from Monomer's reagent labels.*

### Precipitation Constraints

These combinations must be excluded from the search space:

| Combination | Precipitate | Rule |
|---|---|---|
| CaCl2 + KH2PO4/K2HPO4 | Calcium phosphate (insoluble) | Never combine high [Ca2+] with high [phosphate] |
| High MgSO4 + high pH (NaOH) | Magnesium hydroxide | Keep MgSO4 below threshold if pH > 8 |
| FeCl3 + high pH | Iron hydroxide | FeCl3 precipitates above pH ~7 |

### Candidate 3 Components to Optimize

| Priority | Component | Rationale |
|---|---|---|
| Likely | **Glucose** | Primary carbon source. Concentration directly affects growth rate. |
| Likely | **MgSO4** | Essential cofactor. Often rate-limiting in minimal/defined media. |
| Likely | **NaCl** | V. natriegens is a marine halophile. Optimal [NaCl] is critical (1-3% range). |
| Maybe | Tryptone or Yeast Extract | Nitrogen sources — but may be part of basal LBv2 already |
| Maybe | KH2PO4/K2HPO4 | Buffering capacity affects long-term growth |

pH adjusters (HCl/NaOH) are likely fixed parameters, not optimization variables. Final decision comes from Phase 1 Research + scientist input.

---

## 5. Phase 1 Research Questions

These must be answered during the 1-hour research window (1:00-2:00 PM Saturday) before Phase 2 Build begins.

### Q1: What 3 media components are most impactful to optimize?

**Current best answer:** Glucose, MgSO4, NaCl (see candidate table in Section 4).

**Open items:**
- Confirm whether Tryptone/Yeast Extract are already in LBv2 basal and thus fixed
- Validate with scientist input during Phase 1

### Q2: What dilution ranges for each component?

**Current best answer:** TBD — depends on stock concentrations (confirmed day-of).

**Open items:**
- Get stock concentrations from Monomer's reagent labels
- Literature ranges: NaCl 1-3% for V. natriegens, Glucose 0.1-2%, MgSO4 0.1-10 mM
- Must fit within liquid handler volume constraints (Opentrons Flex)

### Q3: DOE or Bayesian optimization?

**Current best answer:** Likely Bayesian (BayBE) — better for iterative closed-loop with limited rounds (~6 max). DOE is better for one-shot characterization.

**Open items:**
- ~~Elnora's MCP may dictate the optimization strategy~~ RESOLVED: Elnora is a literature/protocol agent, not an optimizer. BayBE handles optimization.
- Elnora's MCP servers (PubMed, KEGG, etc.) can inform the DOE vs Bayesian decision with domain context

### Q4: What media components cause precipitation, and how to design against it?

**Current best answer:** Three known constraints (see precipitation table in Section 4). Encode as hard constraints in search space.

**Open items:**
- Confirm if any additional precipitation rules exist for V. natriegens-specific media
- Ask Monomer staff during tutorial

### Phase 1 Checklist

- [ ] Which 3 of 16 reagents to optimize
- [ ] Dilution ranges for each
- [ ] Precipitation avoidance rules (hard constraints)
- [ ] DOE vs. Bayesian optimization decision
- [ ] Understanding of Elnora's MCP capabilities
- [ ] Familiarity with Monomer's MCP from tutorial

---

## 6. Key Constraints

| Constraint | Detail |
|---|---|
| **Robots sleep at midnight** | No experimental runs after 12:00 AM Saturday. Cap rounds at ~6 max. |
| **~45 min per round** | V. natriegens ~10 min doubling time, incubation ~45 min per round |
| **LBv2 basal media** | Baseline control. All optimizations are supplements/modifications to LBv2. |
| **OD600 only readout** | No microscope. Absorbance is the primary metric. Fluorescence TBC. |
| **Elnora integration required** | Not optional — must integrate Elnora's MCP for literature/protocol context. Complementary to BayBE, not a replacement. |
| **Monomer MCP required** | All robot control goes through Monomer's MCP. |
| **Stock concentrations TBD** | Confirmed day-of from Monomer's reagent labels. |

---

## 7. Contacts & Sponsors

| Role | Name | Notes |
|---|---|---|
| Track A leads | **Carter Allen**, **Carmen Kivisild** | Primary contacts for pre-hackathon questions |
| Host | **Monomer Bio** | Provides workcell, reagents, MCP infrastructure |
| Literature/protocol context | **Elnora AI** | Independent SaaS (Carmen Kivisild). 25 MCP servers via Augmented-Nature GitHub org. Protocol generation + domain knowledge, NOT optimization. |
