"""BayBE optimization for CellAI media formulation experiments.

Feeds Round 1 growth rate data into BayBE and recommends Round 2 formulations.
"""

import pandas as pd
from baybe import Campaign
from baybe.objectives import SingleTargetObjective
from baybe.parameters import (
    CategoricalParameter,
    NumericalContinuousParameter,
)
from baybe.searchspace import SearchSpace, SubspaceContinuous
from baybe.targets import NumericalTarget


# === DEFINE SEARCH SPACE ===

base_media = CategoricalParameter(
    name="base_media",
    values=["Semi-Defined", "High Buffer Defined", "LBv2"],
)

# Shared parameters (SD and HB)
yeast_extract = NumericalContinuousParameter(
    name="yeast_extract_g_per_L",
    bounds=(5.0, 15.0),
)
tryptone = NumericalContinuousParameter(
    name="tryptone_g_per_L",
    bounds=(5.0, 15.0),
)

# SD-specific
mops_sd = NumericalContinuousParameter(
    name="mops_mM",
    bounds=(35.0, 100.0),
)

# HB-specific
na_l_glutamate = NumericalContinuousParameter(
    name="na_l_glutamate_mM",
    bounds=(10.0, 50.0),
)

# LBv2-specific
mops_lb = NumericalContinuousParameter(
    name="mops_lb_mM",
    bounds=(50.0, 150.0),
)
kh2po4 = NumericalContinuousParameter(
    name="kh2po4_mM",
    bounds=(10.0, 50.0),
)
glucose = NumericalContinuousParameter(
    name="glucose_g_per_L",
    bounds=(2.0, 10.0),
)

# Build 3 separate campaigns (one per base media) for cleaner optimization
# Each has exactly 3 continuous parameters

# --- Semi-Defined Campaign ---
sd_searchspace = SearchSpace(
    continuous=SubspaceContinuous(
        parameters=[yeast_extract, tryptone, mops_sd]
    ),
)
sd_objective = SingleTargetObjective(
    target=NumericalTarget(name="growth_rate_per_hr", mode="MAX")
)
sd_campaign = Campaign(searchspace=sd_searchspace, objective=sd_objective)

# --- High Buffer Defined Campaign ---
hb_searchspace = SearchSpace(
    continuous=SubspaceContinuous(
        parameters=[yeast_extract, tryptone, na_l_glutamate]
    ),
)
hb_objective = SingleTargetObjective(
    target=NumericalTarget(name="growth_rate_per_hr", mode="MAX")
)
hb_campaign = Campaign(searchspace=hb_searchspace, objective=hb_objective)

# --- LBv2 Campaign ---
lb_searchspace = SearchSpace(
    continuous=SubspaceContinuous(
        parameters=[mops_lb, kh2po4, glucose]
    ),
)
lb_objective = SingleTargetObjective(
    target=NumericalTarget(name="growth_rate_per_hr", mode="MAX")
)
lb_campaign = Campaign(searchspace=lb_searchspace, objective=lb_objective)


# === FEED ROUND 1 DATA ===

# Semi-Defined observations
sd_data = pd.DataFrame([
    {"yeast_extract_g_per_L": 7.0,  "tryptone_g_per_L": 13.0, "mops_mM": 55.0, "growth_rate_per_hr": 0.823255},  # SD-1 (B2)
    {"yeast_extract_g_per_L": 10.0, "tryptone_g_per_L": 7.0,  "mops_mM": 35.0, "growth_rate_per_hr": 0.828949},  # SD-2 (B3)
    {"yeast_extract_g_per_L": 13.0, "tryptone_g_per_L": 10.0, "mops_mM": 45.0, "growth_rate_per_hr": 0.837553},  # SD-3 (B4)
])

# High Buffer Defined observations
hb_data = pd.DataFrame([
    {"yeast_extract_g_per_L": 7.0,  "tryptone_g_per_L": 13.0, "na_l_glutamate_mM": 50.0, "growth_rate_per_hr": 0.901346},  # HB-1 (B5)
    {"yeast_extract_g_per_L": 10.0, "tryptone_g_per_L": 7.0,  "na_l_glutamate_mM": 30.0, "growth_rate_per_hr": 0.852627},  # HB-2 (B6)
    {"yeast_extract_g_per_L": 13.0, "tryptone_g_per_L": 10.0, "na_l_glutamate_mM": 40.0, "growth_rate_per_hr": 0.813991},  # HB-3 (B7)
])

# LBv2 observations
lb_data = pd.DataFrame([
    {"mops_lb_mM": 60.0,  "kh2po4_mM": 50.0, "glucose_g_per_L": 9.0, "growth_rate_per_hr": 0.619012},  # LB-1 (B8)
    {"mops_lb_mM": 80.0,  "kh2po4_mM": 30.0, "glucose_g_per_L": 6.0, "growth_rate_per_hr": 0.763647},  # LB-2 (B9)
    {"mops_lb_mM": 90.0,  "kh2po4_mM": 40.0, "glucose_g_per_L": 4.0, "growth_rate_per_hr": 0.691277},  # LB-3 (B10)
])

print("=" * 60)
print("ROUND 1 RESULTS")
print("=" * 60)
print("\nSemi-Defined (best: SD-3 @ 0.838/hr):")
print(sd_data.to_string(index=False))
print("\nHigh Buffer Defined (best: HB-1 @ 0.901/hr):")
print(hb_data.to_string(index=False))
print("\nLBv2 (best: LB-2 @ 0.764/hr):")
print(lb_data.to_string(index=False))

# Add observations to campaigns
sd_campaign.add_measurements(sd_data)
hb_campaign.add_measurements(hb_data)
lb_campaign.add_measurements(lb_data)

# === GET ROUND 2 RECOMMENDATIONS ===
n_per_media = 3  # 3 wells per base media

print("\n" + "=" * 60)
print("ROUND 2 RECOMMENDATIONS (BayBE)")
print("=" * 60)

print("\n--- Semi-Defined (3 recommendations) ---")
sd_recs = sd_campaign.recommend(batch_size=n_per_media)
print(sd_recs.to_string(index=False))

print("\n--- High Buffer Defined (3 recommendations) ---")
hb_recs = hb_campaign.recommend(batch_size=n_per_media)
print(hb_recs.to_string(index=False))

print("\n--- LBv2 (3 recommendations) ---")
lb_recs = lb_campaign.recommend(batch_size=n_per_media)
print(lb_recs.to_string(index=False))

# === CALCULATE TRANSFER VOLUMES ===
print("\n" + "=" * 60)
print("ROUND 2 TRANSFER VOLUMES (200 uL total, 180 uL media + 20 uL cells)")
print("=" * 60)

# Stock concentrations
YE_STOCK = 100.0    # mg/mL = 100 g/L
TRYP_STOCK = 100.0  # mg/mL = 100 g/L
MOPS_STOCK = 1000.0 # mM (1M)
NAGLUT_STOCK = 1000.0  # mM (1M)
KH2PO4_STOCK = 1000.0  # mM (1M)
GLU_STOCK = 100.0   # mg/mL = 100 g/L
TOTAL_VOL = 200.0   # uL
MEDIA_VOL = 180.0   # uL media portion
CELL_VOL = 20.0     # uL cells

wells = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10"]

print("\nWell | Condition | Base uL | Supp1 uL | Supp2 uL | Supp3 uL | Water uL | Cells uL")
print("-" * 95)

for i, (_, row) in enumerate(sd_recs.iterrows()):
    ye_vol = round(row["yeast_extract_g_per_L"] * TOTAL_VOL / YE_STOCK, 1)
    tryp_vol = round(row["tryptone_g_per_L"] * TOTAL_VOL / TRYP_STOCK, 1)
    mops_vol = round(row["mops_mM"] * TOTAL_VOL / MOPS_STOCK, 1)
    supps = ye_vol + tryp_vol + mops_vol
    base_vol = round(MEDIA_VOL - supps, 1)
    water = 0.0
    if base_vol < 0:
        water = 0.0
        base_vol = round(MEDIA_VOL - supps, 1)
    well = wells[i]
    print(f"{well}   | SD-{i+1}      | {base_vol:>6.1f}  | YE {ye_vol:>5.1f}  | Tryp {tryp_vol:>4.1f} | MOPS {mops_vol:>4.1f} | {water:>7.1f}  | {CELL_VOL:>7.1f}")

for i, (_, row) in enumerate(hb_recs.iterrows()):
    ye_vol = round(row["yeast_extract_g_per_L"] * TOTAL_VOL / YE_STOCK, 1)
    tryp_vol = round(row["tryptone_g_per_L"] * TOTAL_VOL / TRYP_STOCK, 1)
    naglut_vol = round(row["na_l_glutamate_mM"] * TOTAL_VOL / NAGLUT_STOCK, 1)
    supps = ye_vol + tryp_vol + naglut_vol
    base_vol = round(MEDIA_VOL - supps, 1)
    water = 0.0
    if base_vol > 130:
        water = base_vol - 110
        base_vol = 110.0
    well = wells[3 + i]
    print(f"{well}   | HB-{i+1}      | {base_vol:>6.1f}  | YE {ye_vol:>5.1f}  | Tryp {tryp_vol:>4.1f} | NaGl {naglut_vol:>4.1f} | {water:>7.1f}  | {CELL_VOL:>7.1f}")

for i, (_, row) in enumerate(lb_recs.iterrows()):
    mops_vol = round(row["mops_lb_mM"] * TOTAL_VOL / MOPS_STOCK, 1)
    kh2po4_vol = round(row["kh2po4_mM"] * TOTAL_VOL / KH2PO4_STOCK, 1)
    glu_vol = round(row["glucose_g_per_L"] * TOTAL_VOL / GLU_STOCK, 1)
    supps = mops_vol + kh2po4_vol + glu_vol
    base_vol = round(MEDIA_VOL - supps, 1)
    water = 0.0
    if base_vol > 150:
        water = base_vol - 130
        base_vol = 130.0
    well = wells[6 + i]
    print(f"{well}   | LB-{i+1}      | {base_vol:>6.1f}  | MOPS {mops_vol:>4.1f}  | KH2P {kh2po4_vol:>4.1f} | Glu  {glu_vol:>4.1f} | {water:>7.1f}  | {CELL_VOL:>7.1f}")

print(f"\n+ B11  | NB-CTRL   | 180.0   Novel Bio Cyclone                              |     0.0  |    20.0")
print(f"\nTotal: 10 wells, 9 optimized + 1 control")
