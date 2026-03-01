# %% [markdown]
# # BayBE — Cell Culture Media Optimization POC
# Testing BayBE (Merck/EMD) as potential Cell.ai backend infrastructure.
# Key capabilities to evaluate: chemical encoding, iterative DoE, transfer learning.

# %%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from baybe import Campaign
from baybe.targets import NumericalTarget
from baybe.objectives import SingleTargetObjective
from baybe.parameters import (
    NumericalDiscreteParameter,
    SubstanceParameter,
    CategoricalParameter,
)
from baybe.searchspace import SearchSpace
from baybe.recommenders import (
    BotorchRecommender,
    FPSRecommender,
    TwoPhaseMetaRecommender,
)

print("All imports OK — BayBE version:", __import__("baybe").__version__)

# %% [markdown]
# ## 1. Define the Search Space
# Simulating a CHO cell culture media optimization with 5 components.
# Using SubstanceParameter with SMILES to test BayBE's chemical encoding.

# %%
parameters = [
    NumericalDiscreteParameter(
        name="Glucose_gL",
        values=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        tolerance=0.3,
    ),
    NumericalDiscreteParameter(
        name="Glutamine_mM",
        values=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
        tolerance=0.2,
    ),
    NumericalDiscreteParameter(
        name="FBS_pct",
        values=[2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0],
        tolerance=0.5,
    ),
    NumericalDiscreteParameter(
        name="NaHCO3_gL",
        values=[1.5, 2.0, 2.4, 2.8, 3.2, 3.6],
        tolerance=0.1,
    ),
    SubstanceParameter(
        name="GrowthSupplement",
        data={
            "Hydrocortisone": "OC1(C(=O)CO)CCC2C1CCC1C2CC(O)C2(C)C1CCC2=O",
            "Dexamethasone": "OC1(C(=O)CO)CCC2C1CC(F)C1(C)C2CCC2(C)C1CC(=O)C=C2",
            "Putrescine": "NCCCCN",
            "Ethanolamine": "NCCO",
            "Linoleic_acid": "CCCCCC=CCC=CCCCCCCCC(=O)O",
        },
        encoding="MORDRED",
    ),
]

searchspace = SearchSpace.from_product(parameters)
print(f"Search space size: {len(searchspace.discrete.exp_rep)} candidate formulations")
print(f"Parameters: {[p.name for p in parameters]}")

# %% [markdown]
# ## 2. Synthetic Objective Function
# Simulates cell viability (0-100%) as a function of media components.
# Known optimum: Glucose=4.5, Glutamine=2.0, FBS=10%, NaHCO3=2.4, Putrescine supplement.

# %%
OPTIMAL = {
    "Glucose_gL": 4.5,
    "Glutamine_mM": 2.0,
    "FBS_pct": 10.0,
    "NaHCO3_gL": 2.4,
    "GrowthSupplement": "Putrescine",
}

WEIGHTS = {
    "Glucose_gL": 3.0,
    "Glutamine_mM": 5.0,
    "FBS_pct": 1.0,
    "NaHCO3_gL": 8.0,
    "GrowthSupplement": 10.0,
}

def simulate_viability(row: pd.Series, optimal: dict = OPTIMAL, noise_std: float = 2.0) -> float:
    """Synthetic cell viability based on distance from optimal formulation."""
    score = 100.0

    for param in ["Glucose_gL", "Glutamine_mM", "FBS_pct", "NaHCO3_gL"]:
        diff = abs(row[param] - optimal[param])
        norm_range = {"Glucose_gL": 7.0, "Glutamine_mM": 3.5, "FBS_pct": 13.0, "NaHCO3_gL": 2.1}
        score -= WEIGHTS[param] * (diff / norm_range[param]) ** 2 * 25

    supplement_bonus = {
        "Putrescine": 0, "Ethanolamine": -3, "Linoleic_acid": -5,
        "Hydrocortisone": -8, "Dexamethasone": -12,
    }
    score += supplement_bonus.get(row["GrowthSupplement"], -15)

    score += np.random.normal(0, noise_std)
    return float(np.clip(score, 0, 100))

test_row = pd.Series(OPTIMAL)
print(f"Viability at known optimum: {simulate_viability(test_row, noise_std=0):.1f}%")

worst = pd.Series({"Glucose_gL": 1.0, "Glutamine_mM": 4.0, "FBS_pct": 2.0,
                    "NaHCO3_gL": 3.6, "GrowthSupplement": "Hydrocortisone"})
print(f"Viability at worst point:   {simulate_viability(worst, noise_std=0):.1f}%")

# %% [markdown]
# ## 3. Iterative Optimization Loop
# Run 8 rounds of 3 experiments each. Track convergence toward the optimum.

# %%
np.random.seed(42)

target = NumericalTarget(name="CellViability", mode="MAX")
objective = SingleTargetObjective(target=target)

recommender = TwoPhaseMetaRecommender(
    initial_recommender=FPSRecommender(),
    recommender=BotorchRecommender(),
)

campaign = Campaign(searchspace, objective, recommender)

N_ROUNDS = 8
BATCH_SIZE = 3
best_per_round = []
all_results = []

for round_idx in range(N_ROUNDS):
    recommendations = campaign.recommend(batch_size=BATCH_SIZE)

    recommendations["CellViability"] = recommendations.apply(simulate_viability, axis=1)

    campaign.add_measurements(recommendations)
    all_results.append(recommendations.copy())

    best_this_round = recommendations["CellViability"].max()
    best_overall = max(best_this_round, best_per_round[-1] if best_per_round else 0)
    best_per_round.append(best_overall)

    print(f"Round {round_idx + 1}: best this batch = {best_this_round:.1f}%, "
          f"best overall = {best_overall:.1f}%")

print(f"\nTotal experiments: {N_ROUNDS * BATCH_SIZE}")
print(f"Best viability found: {best_per_round[-1]:.1f}%")

# %%
all_df = pd.concat(all_results, ignore_index=True)
print("\n--- Top 5 formulations found ---")
top5 = all_df.nlargest(5, "CellViability")
print(top5[["Glucose_gL", "Glutamine_mM", "FBS_pct", "NaHCO3_gL",
            "GrowthSupplement", "CellViability"]].to_string(index=False))

# %% [markdown]
# ## 4. Convergence Plot

# %%
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(range(1, N_ROUNDS + 1), best_per_round, "o-", linewidth=2, markersize=8)
ax.axhline(y=100, color="green", linestyle="--", alpha=0.5, label="Theoretical max (100%)")
ax.set_xlabel("Optimization Round")
ax.set_ylabel("Best Cell Viability (%)")
ax.set_title("BayBE Convergence — CHO Media Optimization")
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(range(1, N_ROUNDS + 1))
plt.tight_layout()
plt.savefig("/Users/viachealavrudenko/Cell.ai/doc/scrapbook/baybe_convergence.png", dpi=150)
plt.show()
print("Plot saved to doc/scrapbook/baybe_convergence.png")

# %% [markdown]
# ## 5. Transfer Learning Test
# New campaign for a different cell type (HEK293) with a shifted optimum.
# Seed it with data from the CHO campaign to test knowledge transfer.

# %%
OPTIMAL_HEK = {
    "Glucose_gL": 3.0,
    "Glutamine_mM": 3.0,
    "FBS_pct": 8.0,
    "NaHCO3_gL": 2.0,
    "GrowthSupplement": "Ethanolamine",
}

def simulate_viability_hek(row: pd.Series) -> float:
    return simulate_viability(row, optimal=OPTIMAL_HEK, noise_std=2.0)

campaign_hek_cold = Campaign(searchspace, objective, recommender)

campaign_hek_warm = Campaign(searchspace, objective, recommender)
cho_data = all_df.copy()
cho_data["CellViability"] = cho_data.apply(simulate_viability_hek, axis=1)
campaign_hek_warm.add_measurements(cho_data)

N_ROUNDS_TL = 5
best_cold = []
best_warm = []

np.random.seed(123)
for r in range(N_ROUNDS_TL):
    rec_cold = campaign_hek_cold.recommend(batch_size=BATCH_SIZE)
    rec_cold["CellViability"] = rec_cold.apply(simulate_viability_hek, axis=1)
    campaign_hek_cold.add_measurements(rec_cold)
    best_c = rec_cold["CellViability"].max()
    best_cold.append(max(best_c, best_cold[-1] if best_cold else 0))

    rec_warm = campaign_hek_warm.recommend(batch_size=BATCH_SIZE)
    rec_warm["CellViability"] = rec_warm.apply(simulate_viability_hek, axis=1)
    campaign_hek_warm.add_measurements(rec_warm)
    best_w = rec_warm["CellViability"].max()
    best_warm.append(max(best_w, best_warm[-1] if best_warm else 0))

    print(f"Round {r+1} — Cold start: {best_cold[-1]:.1f}% | Warm start: {best_warm[-1]:.1f}%")

# %%
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(range(1, N_ROUNDS_TL + 1), best_cold, "s--", label="Cold start (no prior data)", linewidth=2)
ax.plot(range(1, N_ROUNDS_TL + 1), best_warm, "o-", label="Warm start (CHO data transferred)", linewidth=2)
ax.set_xlabel("Optimization Round")
ax.set_ylabel("Best Cell Viability (%)")
ax.set_title("Transfer Learning — HEK293 Media Optimization")
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xticks(range(1, N_ROUNDS_TL + 1))
plt.tight_layout()
plt.savefig("/Users/viachealavrudenko/Cell.ai/doc/scrapbook/baybe_transfer_learning.png", dpi=150)
plt.show()
print("Plot saved to doc/scrapbook/baybe_transfer_learning.png")

# %% [markdown]
# ## 6. Evaluation Summary
#
# **API Ergonomics:**
# - Campaign/SearchSpace/Objective pattern is clean and intuitive
# - SubstanceParameter with SMILES encoding is the killer feature — no other tool does this
# - TwoPhaseMetaRecommender (exploration then exploitation) is a good default
# - Adding measurements and getting recommendations is a simple 2-method loop
#
# **For Cell.ai product integration:**
# - Campaign object is serializable — can be saved/loaded between sessions
# - Search space definition maps cleanly to a UI form builder
# - The recommend → measure → recommend loop maps to a step-by-step wizard
# - Transfer learning = platform-level advantage (cross-customer learnings)
#
# **Limitations found:**
# - No built-in multi-objective optimization (need BoTorch for that)
# - No biological constraint enforcement (osmolality, pH limits)
# - No built-in visualization
# - Discrete parameter space only (continuous requires BoTorch integration)
