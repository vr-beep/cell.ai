#!/usr/bin/env python3
"""
Pull plate reader data for a given plate ID via the monitor MCP and
write a formatted CSV matching the cellai_tutorial_experiment_plate.csv schema.

Uses Claude Code (subprocess) as the MCP client so the monitor MCP server
configuration in your local Claude Code settings is used automatically.
The subprocess is responsible only for tool calls; all data joining and
formatting is done in Python.

Usage:
    python scripts/monitor_data_processing.py <plate_id> [<plate_id> ...] [-o output.csv] [-d output_dir]

Examples:
    # Plate 1: PLT12V3H4WNRSR6CWJ7A72ODORU7EI
    python scripts/monitor_data_processing.py PLT12V3H4WNRSR6CWJ7A72ODORU7EI
    # Plate 2: PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ
    python scripts/monitor_data_processing.py PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ
    # Plate 3: PLT1RQR2P5DESEEHSKOIUQCNAXH3RA
    python scripts/monitor_data_processing.py PLT1RQR2P5DESEEHSKOIUQCNAXH3RA
"""

import argparse
import csv
import io
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

# Output CSV columns — must match the example in data/
COLUMNS = [
    "culture_id",
    "well",
    "condition_id",
    "plate_id",
    "plate_barcode",
    "status",
    "parent_culture_id",
    "observation_timestamp",
    "absorbance_OD600",
    "cell_concentration_cells_per_mL",
    "reagent_name",
    "reagent_volume_uL",
]

# One row per well — logistic S-curve fit metrics
GROWTH_COLUMNS = [
    "culture_id",
    "well",
    "condition_id",
    "plate_id",
    "plate_barcode",
    "status",
    "parent_culture_id",
    "reagent_name",
    "reagent_volume_uL",
    "n_timepoints",
    "growth_rate_per_hr",
    "t_inflection_hours",
    "max_absorbance_OD600",
    "max_cell_concentration_cells_per_mL",
    "fit_r2",
    "fit_rmse",
]

# One row per (plate, condition_id) — replicate summary
REPLICATE_COLUMNS = [
    "plate_id",
    "plate_barcode",
    "condition_id",
    "reagent_name",
    "n_replicates",
    "mean_growth_rate_per_hr",
    "median_growth_rate_per_hr",
    "variance_growth_rate_per_hr",
    "mean_max_absorbance_OD600",
    "mean_max_cell_concentration_cells_per_mL",
]

# Subprocess prompt: just instruct Claude to call the 3 tools.
# We extract results directly from the stream-json event log — no output needed.
FETCH_PROMPT = """\
Plate ID: {plate_id}

Call these tools in order and stop when done. Do not output anything.

1. mcp__monitor__list_cultures  plate_id="{plate_id}"  limit=500  include=["reagents","parent_culture_id"]
   If next_cursor is not null, call again with the cursor until all pages are fetched.

2. mcp__monitor__get_plate_observations  plate_id="{plate_id}"  dataset_limit=500
   If next_cursor is not null, call again with the cursor until all pages are fetched.

3. For each csv_resource_uri in the get_plate_observations responses, call
   mcp__monitor__read_resource once.
"""

ALLOWED_TOOLS = ",".join([
    "mcp__monitor__list_cultures",
    "mcp__monitor__get_plate_observations",
    "mcp__monitor__read_resource",
])

SUBPROCESS_TIMEOUT_SECONDS = 90
SUBPROCESS_MAX_RETRIES = 3


def fetch_raw(plate_id: str) -> dict:
    """Invoke Claude Code to call MCP tools; extract results from stream-json events."""
    prompt = FETCH_PROMPT.format(plate_id=plate_id)
    cmd = [
        "claude", "-p", prompt,
        "--allowedTools", ALLOWED_TOOLS,
        "--model", "claude-haiku-4-5-20251001",
        "--output-format", "stream-json",
        "--verbose",
    ]
    last_error: Exception | None = None
    for attempt in range(1, SUBPROCESS_MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
            )
            break
        except subprocess.TimeoutExpired:
            last_error = RuntimeError(
                f"claude subprocess timed out after {SUBPROCESS_TIMEOUT_SECONDS}s "
                f"(attempt {attempt}/{SUBPROCESS_MAX_RETRIES}). "
                "Check that the monitor MCP server is reachable."
            )
            if attempt < SUBPROCESS_MAX_RETRIES:
                print(f"  Timeout on attempt {attempt}, retrying...", file=sys.stderr)
    else:
        raise last_error
    if result.returncode != 0:
        print("claude stderr:", result.stderr, file=sys.stderr)
        raise RuntimeError(f"claude exited with code {result.returncode}")

    # Build a map of tool_use_id -> tool_name from assistant events,
    # then collect tool results from user message content blocks.
    tool_id_to_name: dict[str, str] = {}
    # tool_name -> list of parsed result dicts/strings (in call order)
    tool_results: dict[str, list] = {}

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_id_to_name[block["id"]] = block["name"]

        elif event.get("type") == "user":
            for block in event.get("message", {}).get("content", []):
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_use_id = block.get("tool_use_id", "")
                    tool_name = tool_id_to_name.get(tool_use_id, "")
                    raw_content = block.get("content", "")
                    if isinstance(raw_content, str):
                        try:
                            parsed = json.loads(raw_content)
                            # All MCP results are wrapped: {"result": <actual>}
                            if isinstance(parsed, dict) and "result" in parsed:
                                parsed = parsed["result"]
                        except json.JSONDecodeError:
                            parsed = raw_content
                    else:
                        parsed = raw_content
                    tool_results.setdefault(tool_name, []).append(parsed)

    return _assemble_payload(plate_id, tool_results)


def _assemble_payload(plate_id: str, tool_results: dict) -> dict:
    """Build the canonical payload dict from raw tool result lists."""
    # --- cultures ---
    cultures: list[dict] = []
    for result in tool_results.get("mcp__monitor__list_cultures", []):
        if isinstance(result, dict):
            cultures.extend(result.get("items", []))

    # --- plate barcode + csv URIs from observations ---
    # get_plate_observations result: {"items": [{plate_barcode, csv_resource_uri, ...}], ...}
    plate_barcode = ""
    for result in tool_results.get("mcp__monitor__get_plate_observations", []):
        if isinstance(result, dict):
            for item in result.get("items", []):
                if not plate_barcode:
                    plate_barcode = item.get("plate_barcode", "")

    # --- observation CSVs ---
    # read_resource result is unwrapped to the CSV string directly
    observation_csvs: list[str] = []
    for result in tool_results.get("mcp__monitor__read_resource", []):
        if isinstance(result, str) and result.strip():
            observation_csvs.append(result)

    if not cultures:
        raise ValueError("No culture data received from list_cultures tool call.")
    if not observation_csvs:
        raise ValueError("No observation CSV data received from read_resource tool call.")

    return {
        "plate_id": plate_id,
        "plate_barcode": plate_barcode,
        "cultures": cultures,
        "observation_csvs": observation_csvs,
    }


# Conversion factor from absorbance OD600 to cells/mL (per MCP server metadata)
OD600_TO_CELLS_PER_ML = 1_000_000_000


def melt_wide_csv(csv_text: str) -> list[dict]:
    """Convert wide-format plate CSV (timestamp + well columns) to long format.

    Input columns: timestamp, A1, A2, ..., H12
    Output dicts:  observation_timestamp, well, absorbance_OD600,
                   cell_concentration_cells_per_mL
    """
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    rows = []
    for row in reader:
        ts = row.get("timestamp", "")
        for col, val in row.items():
            if col == "timestamp" or val == "" or val is None:
                continue
            od = _num(val)
            rows.append({
                "observation_timestamp": ts,
                "well": col,
                "absorbance_OD600": od,
                "cell_concentration_cells_per_mL": (
                    int(od * OD600_TO_CELLS_PER_ML) if od is not None else None
                ),
            })
    return rows


def build_rows(raw: dict, data_dir: Path) -> list[dict]:
    """Join observation rows with the culture map and normalise to COLUMNS."""
    plate_id = raw["plate_id"]
    plate_barcode = raw["plate_barcode"]

    # Load plate map
    plate_map_path = data_dir / f"{plate_id}_plate_condition_map.csv"
    well_to_condition = {}
    if plate_map_path.exists():
        with open(plate_map_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            signature_to_id = {}
            condition_counters = {}
            for row in reader:
                sig = tuple(sorted((k, v) for k, v in row.items() if k != "well"))
                if sig not in signature_to_id:
                    cond_base = row.get("condition", "Cond")
                    condition_counters[cond_base] = condition_counters.get(cond_base, 0) + 1
                    signature_to_id[sig] = f"{cond_base}_{condition_counters[cond_base]}"
                well_to_condition[row["well"]] = signature_to_id[sig]
    else:
        print(f"Warning: Plate map not found at {plate_map_path}", file=sys.stderr)

    # Build culture map keyed by well
    culture_map: dict[str, dict] = {}
    for c in raw.get("cultures", []):
        culture_map[c["well"]] = c

    # Melt all observation CSV pages from wide to long format
    obs_rows: list[dict] = []
    for csv_text in raw.get("observation_csvs", []):
        obs_rows.extend(melt_wide_csv(csv_text))

    rows: list[dict] = []
    for obs in obs_rows:
        well = obs["well"]
        culture = culture_map.get(well, {})
        reagents = culture.get("reagents") or []
        condition_id = well_to_condition.get(well)

        base = {
            "culture_id": culture.get("id"),
            "well": well,
            "condition_id": condition_id,
            "plate_id": plate_id,
            "plate_barcode": plate_barcode,
            "status": culture.get("status"),
            "parent_culture_id": culture.get("parent_culture_id"),
            "observation_timestamp": obs["observation_timestamp"],
            "absorbance_OD600": obs["absorbance_OD600"],
            "cell_concentration_cells_per_mL": obs["cell_concentration_cells_per_mL"],
        }

        if reagents:
            for r in reagents:
                rows.append({
                    **base,
                    "reagent_name": r.get("name"),
                    "reagent_volume_uL": _num(r.get("volume")),
                })
        else:
            rows.append({**base, "reagent_name": None, "reagent_volume_uL": None})

    rows.sort(key=lambda r: (r["observation_timestamp"] or "", r["well"] or ""))
    return [{col: r.get(col) for col in COLUMNS} for r in rows]


def _num(val):
    """Convert a value to a number, stripping any unit suffix (e.g. '100.0 uL')."""
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        return val
    try:
        return float(str(val).split()[0])
    except (TypeError, ValueError):
        return val


def _logistic(t: np.ndarray, A: float, K: float, r: float, t0: float) -> np.ndarray:
    """4-parameter logistic (Richards) growth model.

    y = A + (K - A) / (1 + exp(-r * (t - t0)))

    A  — lower asymptote: baseline OD from the inoculum at t=0
    K  — upper asymptote: carrying capacity (maximum OD)
    r  — growth rate at the inflection point (hr⁻¹), reported as growth_rate_per_hr
    t0 — inflection time (hr), reported as t_inflection_hours
    """
    return A + (K - A) / (1.0 + np.exp(-r * (t - t0)))


def _fit_logistic(times_hr: list[float], od_values: list[float]):
    """Fit a 4-parameter logistic S-curve to a single well's time series.

    Returns (K, r, t0, r2, rmse). All None when fewer than 4 points are
    available or curve_fit fails to converge.
    """
    t = np.array(times_hr, dtype=float)
    y = np.array(od_values, dtype=float)

    if len(t) < 4:
        return None, None, None, None, None

    A0  = float(np.min(y))                              # seed from observed minimum
    K0  = float(np.max(y)) * 1.1                        # seed slightly above observed max
    mid = A0 + (K0 - A0) / 2.0
    t0_0 = float(t[int(np.argmin(np.abs(y - mid)))])   # time closest to midpoint
    try:
        popt, _ = curve_fit(
            _logistic, t, y,
            p0=[A0, K0, 1.0, t0_0],
            bounds=([0.0, 0.0, 0.0, -np.inf], [np.inf, np.inf, np.inf, np.inf]),
            maxfev=5000,
        )
        A, K, r, t0 = (float(popt[0]), float(popt[1]),
                       float(popt[2]), float(popt[3]))
        y_pred = _logistic(t, *popt)
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
        r2 = round(1.0 - ss_res / ss_tot, 6) if ss_tot > 0 else None
        rmse = round(float(np.sqrt(float(np.mean((y - y_pred) ** 2)))), 6)
        return round(K, 6), round(r, 6), round(t0, 4), r2, rmse
    except Exception:
        return None, None, None, None, None


def _to_unix(ts: str) -> float:
    """Parse ISO 8601 timestamp to Unix seconds."""
    dt = datetime.fromisoformat(ts.strip())
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def estimate_growth(rows: list[dict]) -> list[dict]:
    """Fit a logistic S-curve to each well and return one row per (plate, well).

    Input: rows from build_rows() — one entry per timepoint × reagent × well.
    Output: one dict per well with S-curve fit metrics.
    """
    # Deduplicate to unique (timestamp, OD) per well; keep first-seen culture metadata.
    well_data: dict[tuple, dict] = {}
    for row in rows:
        key = (row["plate_id"], row["well"])
        if key not in well_data:
            well_data[key] = {
                "culture_id": row["culture_id"],
                "well": row["well"],
                "condition_id": row.get("condition_id"),
                "plate_id": row["plate_id"],
                "plate_barcode": row["plate_barcode"],
                "status": row["status"],
                "parent_culture_id": row["parent_culture_id"],
                "_ts_od": {},
                "_reagents": [],
                "_volumes": [],
            }
        ts = row["observation_timestamp"]
        od = row["absorbance_OD600"]
        if ts and od is not None:
            well_data[key]["_ts_od"][ts] = float(od)

        r_name = row.get("reagent_name")
        r_vol = row.get("reagent_volume_uL")
        if r_name and r_name not in well_data[key]["_reagents"]:
            well_data[key]["_reagents"].append(r_name)
            well_data[key]["_volumes"].append(str(r_vol) if r_vol is not None else "")

    growth_rows = []
    for meta in well_data.values():
        reagents = meta.pop("_reagents")
        volumes = meta.pop("_volumes")
        
        meta["reagent_name"] = ", ".join(reagents) if reagents else None
        meta["reagent_volume_uL"] = ", ".join(volumes) if volumes else None
        
        points = sorted(meta.pop("_ts_od").items())
        n = len(points)

        if n == 0:
            growth_rows.append({**meta, "n_timepoints": 0,
                                 "growth_rate_per_hr": None, "t_inflection_hours": None,
                                 "max_absorbance_OD600": None,
                                 "max_cell_concentration_cells_per_mL": None,
                                 "fit_r2": None, "fit_rmse": None})
            continue

        t0_unix = _to_unix(points[0][0])
        times_hr = [(_to_unix(ts) - t0_unix) / 3600.0 for ts, _ in points]
        od_values = [od for _, od in points]

        K, r, t0_fit, r2, rmse = _fit_logistic(times_hr, od_values)
        # Use observed max for readout columns so they always reflect real data,
        # not the potentially extrapolated logistic asymptote.
        obs_max_od = max(od_values)
        growth_rows.append({
            **meta,
            "n_timepoints": n,
            "growth_rate_per_hr": r,
            "t_inflection_hours": t0_fit,
            "max_absorbance_OD600": round(obs_max_od, 6),
            "max_cell_concentration_cells_per_mL": int(obs_max_od * OD600_TO_CELLS_PER_ML),
            "fit_r2": r2,
            "fit_rmse": rmse,
        })

    growth_rows.sort(key=lambda r: (r["plate_id"] or "", r["well"] or ""))
    return [{col: r.get(col) for col in GROWTH_COLUMNS} for r in growth_rows]


def aggregate_replicates(growth_rows: list[dict]) -> list[dict]:
    """Average growth metrics across replicate wells sharing a condition_id.

    Groups by (plate_id, condition_id). Reports mean/median/variance of
    growth_rate_per_hr and mean of max readouts. Wells where the fit failed
    (growth_rate_per_hr is None) are excluded from rate statistics but still
    counted in n_replicates.
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in growth_rows:
        key = (row["plate_id"], row["plate_barcode"], row.get("condition_id"))
        groups[key].append(row)

    summary_rows = []
    for (plate_id, plate_barcode, condition_id), members in sorted(groups.items(), key=lambda x: (x[0][0] or "", x[0][1] or "", x[0][2] or "")):
        rates = [r["growth_rate_per_hr"] for r in members
                 if r["growth_rate_per_hr"] is not None]
        max_ods = [r["max_absorbance_OD600"] for r in members
                   if r["max_absorbance_OD600"] is not None]
        max_concs = [r["max_cell_concentration_cells_per_mL"] for r in members
                     if r["max_cell_concentration_cells_per_mL"] is not None]
        
        reagent_sets = set(r.get("reagent_name") for r in members if r.get("reagent_name"))
        reagent_name_str = " | ".join(sorted(reagent_sets)) if reagent_sets else None

        summary_rows.append({
            "plate_id": plate_id,
            "plate_barcode": plate_barcode,
            "condition_id": condition_id,
            "reagent_name": reagent_name_str,
            "n_replicates": len(members),
            "mean_growth_rate_per_hr": round(statistics.mean(rates), 6) if rates else None,
            "median_growth_rate_per_hr": round(statistics.median(rates), 6) if rates else None,
            "variance_growth_rate_per_hr": (
                round(statistics.variance(rates), 9) if len(rates) >= 2 else None
            ),
            "mean_max_absorbance_OD600": round(statistics.mean(max_ods), 6) if max_ods else None,
            "mean_max_cell_concentration_cells_per_mL": (
                int(statistics.mean(max_concs)) if max_concs else None
            ),
        })

    return [{col: r.get(col) for col in REPLICATE_COLUMNS} for r in summary_rows]


def write_csv(rows: list[dict], path: str, columns: list[str]) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull monitor plate data and compute per-well growth metrics."
    )
    parser.add_argument(
        "plate_ids",
        nargs="+",
        help="One or more plate IDs to fetch (e.g. PLT12V3H4WNRSR6CWJ7A72ODORU7EI)",
    )
    parser.add_argument(
        "-d", "--output-dir", default="data",
        help="Directory for output files (default: data)",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Raw observations CSV path (default: <output_dir>/<first_plate_id>.csv)",
    )
    parser.add_argument(
        "-g", "--growth-output", default=None,
        help="Growth metrics CSV path (default: <output_dir>/<first_plate_id>_growth.csv)",
    )
    parser.add_argument(
        "-r", "--replicates-output", default=None,
        help="Replicate summary CSV path (default: <output_dir>/<first_plate_id>_replicates.csv)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.plate_ids[0]

    raw_path = args.output or str(output_dir / f"{stem}.csv")
    growth_path = args.growth_output or str(output_dir / f"{stem}_growth.csv")
    replicates_path = args.replicates_output or str(output_dir / f"{stem}_replicates.csv")

    all_rows: list[dict] = []
    for plate_id in args.plate_ids:
        print(f"Fetching {plate_id}...", file=sys.stderr)
        raw = fetch_raw(plate_id)
        rows = build_rows(raw, data_dir=output_dir)
        print(f"  {len(rows)} observation row(s)", file=sys.stderr)
        all_rows.extend(rows)

    write_csv(all_rows, raw_path, COLUMNS)
    print(f"Written: {raw_path}", file=sys.stderr)

    print("Fitting S-curves...", file=sys.stderr)
    growth_rows = estimate_growth(all_rows)
    print(f"  {len(growth_rows)} well(s) fitted", file=sys.stderr)
    write_csv(growth_rows, growth_path, GROWTH_COLUMNS)
    print(f"Written: {growth_path}", file=sys.stderr)

    print("Aggregating replicates...", file=sys.stderr)
    replicate_rows = aggregate_replicates(growth_rows)
    print(f"  {len(replicate_rows)} reagent group(s)", file=sys.stderr)
    write_csv(replicate_rows, replicates_path, REPLICATE_COLUMNS)
    print(f"Written: {replicates_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
