# BayBE Deep Dive: Configuration, Papers, and Best Practices

> Research compiled March 11, 2026. Sources cited inline.

---

## 1. Key Papers

### BayBE Paper (Digital Discovery, 2025)
- **Title:** "BayBE: a Bayesian Back End for experimental planning in the low-to-no-data regime"
- **Authors:** Martin Fitzner, Adrian Sosic, Alexander V. Hopp et al. (Merck KGaA)
- **Key result:** Chemical encodings reduce experiments to reach 90% yield from 37 to 16 iterations (~57% reduction vs. one-hot encoding)
- **URL:** https://pubs.rsc.org/en/content/articlehtml/2025/dd/d5dd00050e

### Nature Communications Cell Culture Paper (2025)
- **Title:** "Accelerating cell culture media development using Bayesian optimization-based iterative experimental design"
- **Authors:** Harini Narayanan, J. Christopher Love (MIT Koch Institute, Broad Institute)
- **Method:** Custom BO with GP surrogates and UCB acquisition (NOT BayBE itself)
- **Key claim:** "3-30x fewer experiments" than standard DOE (3x for 4 factors, 30x for 8-9 factors)
- **Cell types:** PBMCs (T cells, B cells, NK cells), *K. phaffii* yeast
- **PBMC:** 4 iterations, 24 experiments; media blends + 8 cytokines
- **K. phaffii:** 7 iterations, 90 experiments; 2.5-3x improvement in recombinant protein production
- **URL:** https://www.nature.com/articles/s41467-025-61113-5

### Cellular Agriculture / 181% Paper (Biotechnology & Bioengineering, 2022)
- **Title:** "Multi-information source Bayesian optimization of culture media for cellular agriculture"
- **Authors:** Cosenza, Astudillo, Frazier, Baar, Block (UC Davis, Cornell)
- **Method:** Multi-information source BO with Gaussian Processes (NOT BayBE)
- **Cell type:** Murine C2C12 cells (cultured meat)
- **14 media components** optimized
- **Results:** 181% more cells than commercial DMEM; 38% fewer experiments than DOE (81 vs 133)
- **Structure:** Initial Latin Hypercube (10 experiments) + 7 sequential BO rounds
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9541924/

### Autonomous Lab for Biotechnology (Scientific Reports, Feb 2025)
- First real-world closed-loop medium condition optimization
- BO to tune CaCl2, MgSO4, CoCl2, ZnSO4 for recombinant *E. coli*
- Full loop: culturing -> preprocessing -> measurement -> analysis -> hypothesis
- **URL:** https://www.nature.com/articles/s41598-025-89069-y

---

## 2. BayBE Architecture

**Repo:** https://github.com/emdgroup/baybe (Apache 2.0, Merck KGaA)

### Core Loop
```
Surrogate model update -> Acquisition function maximization -> Objective evaluation -> Data update
```

### Campaign Workflow
```python
from baybe import Campaign
from baybe.targets import NumericalTarget
from baybe.objectives import SingleTargetObjective
from baybe.parameters import NumericalDiscreteParameter
from baybe.searchspace import SearchSpace

target = NumericalTarget(name="GrowthRate", mode="MAX")
objective = SingleTargetObjective(target=target)

parameters = [
    NumericalDiscreteParameter(name="NaCl_gL", values=[10, 15, 20, 25, 30, 35]),
    NumericalDiscreteParameter(name="Glucose_gL", values=[0, 1, 5, 10, 15, 20]),
    NumericalDiscreteParameter(name="YeastExtract_gL", values=[2, 4, 6, 8, 10]),
]
searchspace = SearchSpace.from_product(parameters)

campaign = Campaign(searchspace=searchspace, objective=objective)
df = campaign.recommend(batch_size=14)  # 14 conditions per plate
# ... run experiments, collect growth rates ...
df["GrowthRate"] = [0.42, 0.38, ...]
campaign.add_measurements(df)
# Repeat
```

**Critical batch_size rule:** Recommendations are jointly optimized for the requested batch_size. You must run ALL recommended experiments — using a subset is "strongly discouraged."

### Parameter Types
| Type | Use Case |
|------|----------|
| `NumericalDiscreteParameter` | Discrete concentration levels (e.g., [10, 15, 20, 25, 30, 35] g/L) |
| `NumericalContinuousParameter` | Bounded continuous ranges |
| `CategoricalParameter` | Categorical choices with optional encodings |
| `SubstanceParameter` | Chemical structures via SMILES |
| `TaskParameter` | Transfer learning across related tasks |

### Recommenders
- **BotorchRecommender:** Primary Bayesian recommender, joint batch optimization
- **TwoPhaseMetaRecommender:** Random/space-filling first, then Bayesian after `switch_after` measurements. **Ideal for hackathon: random exploration round 1, Bayesian from round 2.**
- **RandomRecommender / FPSRecommender:** For initialization or baselines

### Surrogate Models
- GaussianProcessSurrogate (default) — configurable kernels: RBF, Matern, periodic, polynomial
- BayesianLinearSurrogate, RandomForestSurrogate, NGBoostSurrogate

### Acquisition Functions
- Single-point: ExpectedImprovement, LogExpectedImprovement, PosteriorMean, UpperConfidenceBound
- **Batch (what we need):** qExpectedImprovement, qUpperConfidenceBound, qThompsonSampling, qKnowledgeGradient
- Multi-objective: qExpectedHypervolumeImprovement

### Serialization
Full JSON serialization via `campaign.to_json()` / `Campaign.from_json()` for persistence across rounds.

---

## 3. BayBE Constraints

### Discrete Constraints
| Constraint | Use Case |
|-----------|----------|
| `DiscreteExcludeConstraint` | Remove specific combos (e.g., high NaCl + high Glucose if precipitation) |
| `DiscreteSumConstraint` | Fractions must sum to 1.0 |
| `DiscreteProductConstraint` | Product conditions on parameter values |
| `DiscreteCardinalityConstraint` | Control how many parameters are "active" (non-zero) |
| `DiscreteDependenciesConstraint` | Conditional parameters |
| `DiscreteCustomConstraint` | Arbitrary Python filter (not serializable) |

### Continuous Constraints
| Constraint | Use Case |
|-----------|----------|
| `ContinuousLinearConstraint` | Linear equality/inequality (e.g., total volume = 1 mL) |
| `ContinuousCardinalityConstraint` | Limit active continuous parameters |

**Limitation:** BayBE does NOT support hybrid constraints on mixed discrete-continuous parameters simultaneously.

---

## 4. BayBE on Robotic Workcells

### Merck KGaA Internal Use
- Powers **BayChem**, a self-service experimental planner at Merck
- Powers a closed-loop platform that optimizes chemical reactions autonomously

### Acceleration Consortium (U of Toronto)
- Since December 2023, testing BayBE in polymer and formulation self-driving labs
- March 2024 hackathon with 120 participants benchmarked BayBE vs proprietary alternatives
- **URL:** https://acceleration.utoronto.ca/news/collaboration-update-the-acceleration-consortiums-self-driving-labs-using-mercks-baybe-in-their-automated-workflows

### No published peer-reviewed robotic integration paper yet
The Nature Comms and Biotech & Bioeng papers used custom BO code, not BayBE. BayBE's robotic integration remains at "announced capability" stage in public literature.

---

## 5. Practical Recommendations for Cell.ai

1. **Use `NumericalDiscreteParameter`** for NaCl, Glucose, Yeast Extract with discrete concentration steps
2. **`TwoPhaseMetaRecommender`** for round 1 (random exploration) -> round 2+ (Bayesian)
3. **`batch_size=14`** to match plate capacity (14 testable conditions + 1 control)
4. **Expect convergence in 2-4 rounds** with 3 components (literature shows 3-7 rounds for 4-14 components)
5. **The 3-30x efficiency claim scales with dimensionality** — with only 3 components, expect closer to 3x
6. **Serialize campaign state between rounds** with `to_json()` — critical for hackathon reliability
7. **No volume/precipitation constraints needed in BayBE** — handle those in the compiler layer instead
