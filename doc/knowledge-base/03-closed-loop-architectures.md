# Closed-Loop Lab Architectures: Patterns, Failure Modes, and Best Practices

> Research compiled March 11, 2026. Sources cited inline.

---

## 1. Key Architecture Papers

### ChemOS 2.0 (Aspuru-Guzik group, 2024)
Definitive orchestration architecture for chemical self-driving labs. Treats the lab as an "operating system" combining ab initio calculations, experimental orchestration, and statistical algorithms. Uses **SiLA2 client/server protocol** for device control. Includes web GUI, Bayesian optimizer, DFT workflow manager, and SQL database.
- Source: https://www.cell.com/matter/abstract/S2590-2385(24)00195-4

### Atlas (Aspuru-Guzik group, 2025)
Application-agnostic Python library for BO in SDLs. Key architecture: **ask-tell pattern** where `ask()` generates parameters, user executes, `tell()` feeds results back. Handles `NaN` measurement failures via variational GP classification. Supports pending experiment tracking for async batch execution.
- Source: https://pubs.rsc.org/en/content/articlehtml/2025/dd/d4dd00115j

### LIRA Module (Communications Chemistry, 2025)
Localization, Inspection, and Reasoning for autonomous workflows. Addresses the open-loop problem: most SDL robot manipulation lacks real-time error detection/correction. Enables automatic retries, task reordering, and replanning based on visual feedback.
- Source: https://www.nature.com/articles/s42004-025-01770-1

---

## 2. The Core Loop Pattern (Cell.ai Architecture)

```
BayBE.recommend(batch_size=14)
    ↓
Compiler (g/L → µL volumes for 1 mL stock)
    ↓
Monomer MCP: create_media_mixture (Opentrons Flex)
    ↓
Monomer MCP: media_exchange (dispense 200 µL to wells)
    ↓
Monomer MCP: incubate (STX-220, 37°C, 2-4 hours)
    ↓
Monomer MCP: plate_read (Tecan Infinite, OD600)
    ↓
Parser: blank subtraction → growth rate calculation
    ↓
BayBE.add_measurements(growth_rates)
    ↓
Repeat
```

### State Management Between Rounds
- **BayBE campaigns are fully serializable** — `to_json()` / `from_json()` for pause/resume
- Atlas uses separate `Planner` (optimization state) and `Campaign` (data trajectory) objects
- ChemOS 2.0 uses SQL database for persistent state across all components

---

## 3. Common Failure Modes

### MCP/API Integration Failures
- MCPs are still nascent in lab automation. SF Lab Automation Hackathon (June 2025) found that most participants had zero prior MCP experience.
- The Opentrons MCP server (github.com/yerbymatey/opentrons-mcp) is community-built, not official.
- **Key failure: state desynchronization** between the MCP client's model of the robot and the robot's actual state (tip attached vs. not, liquid level tracking).

### Plate Reader Parsing Issues
- OD600 readings come in manufacturer-specific formats (CSV, XML, proprietary)
- **Path length correction is critical:** 96-well plate readings are NOT equivalent to 1 cm cuvette readings. Typical well path length is ~0.3-0.5 cm depending on volume.
- Blanking strategy: media-only blanks must match exact composition of each experimental well

### Liquid Handler Volume Accuracy (Opentrons Flex)

| Pipette | Tip | Volume | Accuracy (%D) | Precision (%CV) |
|---------|-----|--------|---------------|-----------------|
| 1ch 50µL | 50µL | **1 µL** | **±8.00%** | **7.00%** |
| 1ch 50µL | 50µL | 10 µL | ±1.50% | 0.50% |
| 1ch 50µL | 50µL | 50 µL | ±1.25% | 0.40% |
| 8ch 50µL | 50µL | **1 µL** | **±10.00%** | **8.00%** |
| 8ch 50µL | 50µL | 10 µL | ±2.50% | 1.00% |
| 8ch 1000µL | 50µL | **5 µL** | **±8.00%** | **4.00%** |
| 8ch 1000µL | 200µL | 200 µL | ±1.00% | 0.25% |
| 96ch | 50µL | **5 µL** | **±10.00%** | **5.00%** |
| 96ch | 200µL | 200 µL | ±1.50% | 1.25% |

**DESIGN RULE: Never dispense below 5 µL. Ideally keep all volumes above 10 µL for reproducibility.**

Volume modes for 50 µL pipettes:
- Low-volume mode (1-4.9 µL): min 1 µL, max 30 µL, push-out 7 µL
- Standard mode (5-50 µL): min 5 µL, max 50 µL, push-out 2 µL
- Must call `configure_for_volume()` before `pick_up_tip()` and when pipette contains no liquid

### Incubation Timing Issues
- Even 5-minute delays compound significantly with V. natriegens (~10 min doubling)
- 96-well plate edge wells evaporate faster during incubation, confounding OD600
- Temperature equilibration when moving plates in/out affects growth

### State Machine Pitfalls
- Open-loop execution (no error detection between steps) is the default in most workcells — primary cause of cascading failures
- Missing "safe state" definitions: what happens if a step fails mid-transfer?

---

## 4. g/L to µL Conversion — Best Practices & Pitfalls

### The Core Calculation

```
V_stock (µL) = (C_target / C_stock) × V_final (µL)

Where:
  C_target = desired final concentration (g/L)
  C_stock  = stock solution concentration (g/L)
  V_final  = final volume (µL) — in our case, 1000 µL (1 mL)
```

### Common Pitfalls

1. **Unit mixing:** 1 g/L = 1 mg/mL = 0.1% w/v. NaCl stock is 5M = 292.2 g/L (not mg/mL).
2. **Final volume accounting:** If adding 3 supplements to 1000 µL, MOPS fill volume = 1000 - V_tryptone - V_YE - V_NaCl - V_glucose. All components must sum to exactly 1000 µL.
3. **Pipette minimum constraint:** If calculation gives <5 µL, either (a) make a more dilute intermediate stock, or (b) increase final volume.
4. **Serial dilution for large ratios:** If stock is 100 g/L and target is 0.01 g/L, use two 1:100 steps, not one 1:10,000 dilution.
5. **Density assumption:** 1 ppm = 1 mg/L only when solution density ≈ 1 g/mL. High-salt solutions (like NaCl at 35 g/L) have density >1.
6. **NaCl is molar, not mg/mL:** Stock is 5M (292.2 mg/mL = 292.2 g/L). To get 10 g/L NaCl in 1 mL: V = (10/292.2) × 1000 = 34.2 µL. This is above the 10 µL accuracy threshold — good.

### Worked Example (Initial Recipe, 1 mL total)

| Component | Target (g/L) | Stock (g/L) | Volume (µL) | Calculation |
|-----------|-------------|-------------|-------------|-------------|
| Tryptone | 10 | 100 | 100.0 | (10/100) × 1000 |
| Yeast Extract | 5 | 100 | 50.0 | (5/100) × 1000 |
| NaCl | 10 | 292.2 | 34.2 | (10/292.2) × 1000 |
| Glucose | 0 | 100 | 0.0 | (0/100) × 1000 |
| MOPS pH 7 | fill | — | **815.8** | 1000 - 100 - 50 - 34.2 - 0 |
| **Total** | | | **1000.0** | |

### Volume Bounds Check (for BayBE search space)

| Component | Min g/L | Max g/L | Min µL | Max µL | Above 10 µL? |
|-----------|---------|---------|--------|--------|---------------|
| NaCl | 10 | 35 | 34.2 | 119.8 | YES |
| Glucose | 1 | 20 | 10.0 | 200.0 | YES (barely at min) |
| Yeast Extract | 2 | 10 | 20.0 | 100.0 | YES |
| Tryptone (fixed) | 10 | 10 | 100.0 | 100.0 | YES |
| MOPS (fill) | — | — | 480.2 | 835.8 | YES |

**All volumes are above the 10 µL Opentrons accuracy threshold.** Glucose at 1 g/L = exactly 10 µL — borderline. Consider setting Glucose minimum to 2 g/L (20 µL) for better accuracy.

---

## 5. 96-Well Plate Layout — Best Practices

### Edge Effect Facts
- Corner wells: **26-34% reduction** in metabolic activity
- Outer perimeter wells: **16-35% reduction** (manufacturer-dependent)
- Effect extends up to 3 rows deep on some plate brands
- Primary cause: differential evaporation during incubation
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8024881/

### Cell.ai Plate Layout (60 usable wells)

```
    1  2  3  4  5  6  7  8  9  10 11 12
A  [------------ BUFFER (edge effect) -----------]
B  | C1  C1  C1  C1b | C2  C2  C2  C2b | C3 ... |
C  | C5  C5  C5  C5b | C6  C6  C6  C6b | C7 ... |
D  | C9  C9  C9  C9b | C10 ...                   |
E  | C13 C13 C13 C13b| C14 C14 C14 C14b|         |
F  | CTL CTL CTL CTLb |                           |
G  |                  (remaining inner wells)      |
H  [------------ BUFFER (edge effect) -----------]

C1-C14 = optimization conditions (3 replicates + 1 blank each)
CTL = initial recipe control (3 replicates + 1 blank)
b = blank (media only, no cells)
```

### Mitigation Strategies
- Fill outer wells with sterile buffer/water as evaporation barriers
- Use plates with moats (e.g., Thermo Nunc Edge 2.0)
- Wrap plates loosely during incubation
- Pre-equilibrate plates at incubation temperature for 15-60 min before inoculation
- **Randomize replicate positions** across the plate to cancel residual gradients

Sources:
- https://www.thermofisher.com/blog/cellculture/reducing-the-edge-effect/
- https://www.wellplate.com/three-ways-reduce-microplate-edge-effect/

---

## 6. Error Handling Patterns

### Atlas Pattern
Accept `NaN` for failed measurements; use feasibility-aware acquisition functions to avoid infeasible regions in future rounds.

### LIRA Pattern
Visual inspection after each step; automatic retry, task reordering, or replanning based on detected failures.

### Confidence-Based Routing
High-confidence actions proceed autonomously; low-confidence or anomalous results trigger human review.

### Human-in-the-Loop Fallback
- **Approval gates** at irreversible decisions (before dispensing, before starting new round)
- **Confidence routing:** If optimizer suggests parameters outside safe range, pause for review
- **Parallel feedback:** Non-blocking human oversight — log decisions for async review while continuing
- Source: https://www.permit.io/blog/human-in-the-loop-for-ai-agents-best-practices-frameworks-use-cases-and-demo

---

## 7. Elnora AI & Augmented Nature

### Elnora AI (elnora.ai)
- Autonomous AI agent for biomedical lab protocol generation and optimization
- Capabilities: literature search, database queries, protocol drafting, learning from outcomes
- Domains: cell culture (iPSC, organoids, 3D), assay development, transfection/CRISPR, protein expression
- Integration: REST APIs and MCP servers; connects to Benchling, LIMS, Slack, PubMed
- Outputs: human-readable, AI-readable, or robot-readable formats
- Source: https://elnora.ai/ai-agent

### Augmented Nature (github.com/Augmented-Nature)
- 20+ MCP servers for biological/chemical databases (all JavaScript)
- Notable: ChEMBL (77 stars), PubChem (35 stars), PDB (21 stars), Reactome, OpenTargets, BioOntology, GeneOntology, AlphaFold, UniProt, STRING-db, KEGG, ClinicalTrials, NCBI-Datasets
- Source: https://www.augmentednature.ai/
