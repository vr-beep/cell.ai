"""Compile conditions (final concentrations) into Monomer transfer_array JSON."""
from __future__ import annotations

import json
from typing import Any

TOTAL_VOL_UL = 200
CELL_VOL_UL = 20
REAGENT_VOL_UL = TOTAL_VOL_UL - CELL_VOL_UL
MIN_PIPETTE_UL = 5
MAX_TRANSFERS = 40

STOCKS = {
    "yeast_extract": {"src_well": "A1"},
    "tryptone":      {"src_well": "A2"},
    "mops":          {"src_well": "A3"},
    "na_l_glut":     {"src_well": "A4"},
    "kh2po4":        {"src_well": "B1"},
    "glucose":       {"src_well": "B2"},
    "nacl":          {"src_well": "B3"},
    "mgso4":         {"src_well": "B4"},
    "water":         {"src_well": "C1"},
}

BASE_MEDIA_WELLS = {
    "Semi-Defined Media":         "D1",
    "High Buffer Defined Media":  "D2",
    "Prepared LBv2 Media":        "D3",
    "Novel Bio NBxCyclone Media": "D4",
}

CELL_SOURCE_WELL = "A1"


def compile_protocol(conditions_json: str, wells: list[str]) -> dict:
    conditions = json.loads(conditions_json) if isinstance(conditions_json, str) else conditions_json

    if len(conditions) > len(wells):
        return {"error": f"More conditions ({len(conditions)}) than wells ({len(wells)})"}

    all_transfers: list[dict[str, Any]] = []
    well_summaries: list[dict] = []

    for i, cond in enumerate(conditions):
        dst_well = wells[i]
        base_media = cond.get("base_media", "High Buffer Defined Media")
        base_vol = float(cond.get("base_media_vol", 110))

        transfers_for_well: list[dict[str, Any]] = []
        reagent_vol_total = base_vol

        # Base media
        transfers_for_well.append({
            "src_plate": "reagent",
            "src_well": BASE_MEDIA_WELLS.get(base_media, "D1"),
            "dst_plate": "experiment", "dst_well": dst_well,
            "volume": round(base_vol, 1), "new_tip": "once", "blow_out": True,
        })

        # Reagent spikes (values assumed in µL)
        for reagent_name, stock_info in STOCKS.items():
            if reagent_name == "water":
                continue
            val = cond.get(reagent_name, 0)
            if val is None or float(val) <= 0:
                continue
            vol = float(val)
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
        water_vol = REAGENT_VOL_UL - reagent_vol_total
        if water_vol >= MIN_PIPETTE_UL:
            transfers_for_well.append({
                "src_plate": "reagent",
                "src_well": STOCKS["water"]["src_well"],
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
            "volume": CELL_VOL_UL, "new_tip": "always", "blow_out": False,
            "post_mix_volume": 40, "post_mix_reps": 5,
        })

        all_transfers.extend(transfers_for_well)
        well_summaries.append({
            "well": dst_well, "base_media": base_media,
            "reagent_vol": round(reagent_vol_total, 1),
            "water_vol": round(max(0, water_vol), 1),
            "total": round(reagent_vol_total + max(0, water_vol) + CELL_VOL_UL, 1),
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
