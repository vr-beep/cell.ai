"""Compile conditions (final concentrations) into Monomer transfer_array JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TOTAL_VOL_UL = 200
CELL_VOL_UL = 20  # default, can be overridden per-condition via "cells" key
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL
MIN_PIPETTE_UL = 5
MAX_TRANSFERS = 50  # Monomer docs say 40, but real workcell accepts up to 50

# Real Team Elnora Reagent Stocks plate layout (MEDIA_20260304_204904_392102)
# Verified from Arne's MCP session with real workcell
STOCKS = {
    "yeast_extract": {"conc_mg_ml": 100, "unit": "g/L", "src_well": "C4"},
    "tryptone":      {"conc_mg_ml": 100, "unit": "g/L", "src_well": "C3"},  # not on plate — placeholder
    "mops":          {"conc_mM": 1000,   "unit": "mM",  "src_well": "C1"},
    "na_l_glut":     {"conc_mM": 1000,   "unit": "mM",  "src_well": "C3"},  # not on plate — placeholder
    "kh2po4":        {"conc_mM": 1000,   "unit": "mM",  "src_well": "C3"},  # not on plate — placeholder
    "glucose":       {"conc_mg_ml": 100, "unit": "g/L", "src_well": "C2"},
    "nacl":          {"conc_mM": 5000,   "unit": "mM",  "src_well": "B4"},
    "mgso4":         {"conc_mM": 1000,   "unit": "mM",  "src_well": "D2"},
    "nh4so4":        {"conc_mM": 1000,   "unit": "mM",  "src_well": "D1"},
    "trace_metals":  {"conc_x": 1000,    "unit": "x",   "src_well": "D3"},
    "glycerol":      {"conc_pct": 10,    "unit": "%",   "src_well": "D4"},
    "water":         {"src_well": "B3"},
}

# Real base media well mapping on Team Elnora Reagent Stocks plate
BASE_MEDIA_WELLS = {
    "Novel Bio NBxCyclone Media": "A1",
    "Prepared LBv2 Media":        "A2",
    "Defined-Minimal Media":      "A3",
    "Semi-Defined Media":         "A4",
    "High Buffer Defined Media":  "B1",
    "Defined-Glycerol":           "B2",
}

CELL_SOURCE_WELL = "A1"
REAGENT_PLATE_NAME = "Team Elnora Reagent Stocks"

_CONFIG_PATH = Path(__file__).parent.parent.parent / "data" / "reagent_plate_map.json"


def _load_plate_config():
    """Load plate config from JSON if available, otherwise use hardcoded defaults."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("stocks", STOCKS), cfg.get("base_media_wells", BASE_MEDIA_WELLS)
    return STOCKS, BASE_MEDIA_WELLS


def _calc_vol_ul(final_conc: float, stock: dict) -> float:
    """Calculate uL of stock needed for final concentration in TOTAL_VOL_UL."""
    if "conc_mM" in stock:
        return (final_conc / stock["conc_mM"]) * TOTAL_VOL_UL
    elif "conc_mg_ml" in stock:
        return (final_conc / stock["conc_mg_ml"]) * TOTAL_VOL_UL
    return 0.0


def compile_protocol(conditions_json: str, wells: list[str]) -> dict:
    conditions = json.loads(conditions_json) if isinstance(conditions_json, str) else conditions_json

    if len(conditions) > len(wells):
        return {"error": f"More conditions ({len(conditions)}) than wells ({len(wells)})"}

    stocks, base_media_wells = _load_plate_config()

    all_transfers: list[dict[str, Any]] = []
    well_summaries: list[dict] = []

    for i, cond in enumerate(conditions):
        dst_well = wells[i]
        base_media = cond.get("base_media", "High Buffer Defined Media")
        has_vol_key = "base_media_vol" in cond
        base_vol = float(cond.get("base_media_vol", 110))
        cell_vol = float(cond.get("cells", CELL_VOL_UL))
        reagent_budget = TOTAL_VOL_UL - cell_vol

        transfers_for_well: list[dict[str, Any]] = []
        reagent_vol_total = base_vol

        # Base media
        transfers_for_well.append({
            "src_plate": "reagent",
            "src_well": base_media_wells.get(base_media, "D1"),
            "dst_plate": "experiment", "dst_well": dst_well,
            "volume": round(base_vol, 1), "new_tip": "once", "blow_out": True,
        })

        # Reagent spikes
        for reagent_name, stock_info in stocks.items():
            if reagent_name == "water":
                continue
            val = cond.get(reagent_name, 0)
            if val is None or float(val) <= 0:
                continue
            if has_vol_key:
                vol = float(val)  # Already in uL (BayBE path)
            else:
                vol = _calc_vol_ul(float(val), stock_info)  # Convert conc -> uL (Elnora path)
            if vol < MIN_PIPETTE_UL:
                continue
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": stock_info["src_well"],
                "dst_plate": "experiment", "dst_well": dst_well,
                "volume": round(vol, 1), "new_tip": "once", "blow_out": True,
            })
            reagent_vol_total += vol

        # Water fill
        water_vol = reagent_budget - reagent_vol_total
        if water_vol >= MIN_PIPETTE_UL:
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": stocks["water"]["src_well"],
                "dst_plate": "experiment", "dst_well": dst_well,
                "volume": round(water_vol, 1), "new_tip": "once", "blow_out": True,
            })
        elif water_vol < 0:
            water_vol = 0

        # Cell seeding
        transfers_for_well.append({
            "src_plate": "cell_culture_stock",
            "src_well": CELL_SOURCE_WELL,
            "dst_plate": "experiment", "dst_well": dst_well,
            "volume": cell_vol, "new_tip": "always", "blow_out": False,
            "pre_mix_volume": 200, "pre_mix_reps": 3,
            "post_mix_volume": min(80, cell_vol), "post_mix_reps": 3,
        })

        all_transfers.extend(transfers_for_well)
        well_summaries.append({
            "well": dst_well, "base_media": base_media,
            "reagent_vol": round(reagent_vol_total, 1),
            "water_vol": round(max(0, water_vol), 1),
            "total": round(reagent_vol_total + max(0, water_vol) + cell_vol, 1),
        })

    errors = []
    if len(all_transfers) > MAX_TRANSFERS:
        errors.append(f"Too many transfers: {len(all_transfers)} > {MAX_TRANSFERS}")
    for ws in well_summaries:
        if abs(ws["total"] - TOTAL_VOL_UL) > 1.0:
            errors.append(f"Well {ws['well']}: total={ws['total']} (expected {TOTAL_VOL_UL})")

    return {
        "transfer_array": all_transfers,
        "n_transfers": len(all_transfers),
        "well_summaries": well_summaries,
        "errors": errors,
    }
