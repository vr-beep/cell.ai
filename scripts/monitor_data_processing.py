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
    python scripts/monitor_data_processing.py PLT12V3H4WNRSR6CWJ7A72ODORU7EI
    python scripts/monitor_data_processing.py PLT_A PLT_B -o results.csv
"""

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

# Output CSV columns — must match the example in data/
COLUMNS = [
    "culture_id",
    "well",
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

SUBPROCESS_TIMEOUT_SECONDS = 120


def fetch_raw(plate_id: str) -> dict:
    """Invoke Claude Code to call MCP tools; extract results from stream-json events."""
    prompt = FETCH_PROMPT.format(plate_id=plate_id)
    try:
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--allowedTools", ALLOWED_TOOLS,
                "--model", "claude-haiku-4-5-20251001",
                "--output-format", "stream-json",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"claude subprocess timed out after {SUBPROCESS_TIMEOUT_SECONDS}s. "
            "Check that the monitor MCP server is reachable."
        )
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


def build_rows(raw: dict) -> list[dict]:
    """Join observation rows with the culture map and normalise to COLUMNS."""
    plate_id = raw["plate_id"]
    plate_barcode = raw["plate_barcode"]

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

        base = {
            "culture_id": culture.get("id"),
            "well": well,
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


def write_csv(rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pull monitor plate data into a formatted CSV via Claude Code + MCP."
    )
    parser.add_argument(
        "plate_ids",
        nargs="+",
        help="One or more plate IDs to fetch (e.g. PLT12V3H4WNRSR6CWJ7A72ODORU7EI)",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output CSV path (default: <output_dir>/<first_plate_id>.csv)",
    )
    parser.add_argument(
        "-d", "--output-dir", default="data",
        help="Directory to save the CSV if --output is not specified (default: data)",
    )
    args = parser.parse_args()

    all_rows: list[dict] = []
    for plate_id in args.plate_ids:
        print(f"Fetching {plate_id}...", file=sys.stderr)
        raw = fetch_raw(plate_id)
        rows = build_rows(raw)
        print(f"  {len(rows)} row(s)", file=sys.stderr)
        all_rows.extend(rows)

    if args.output:
        output_path = args.output
    else:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{args.plate_ids[0]}.csv")

    write_csv(all_rows, output_path)
    print(f"Written: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
