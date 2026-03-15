"""Tests for protocol compiler — conditions to transfer_array."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_compile_single_condition():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    assert result["n_transfers"] > 0
    assert len(result["errors"]) == 0
    assert result["well_summaries"][0]["well"] == "B2"


def test_compile_total_volume_is_200():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    total = result["well_summaries"][0]["total"]
    assert abs(total - 200) < 1.0, f"Total should be 200, got {total}"


def test_compile_includes_cell_seeding():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2"])
    cell_transfers = [t for t in result["transfer_array"]
                      if t["src_plate"] == "cell_culture_stock"]
    assert len(cell_transfers) == 1
    assert cell_transfers[0]["volume"] == 20
    assert cell_transfers[0]["new_tip"] == "always"


def test_compile_too_many_conditions_errors():
    from tools.compiler import compile_protocol
    conditions = [{"base_media_vol": 110} for _ in range(5)]
    result = compile_protocol(json.dumps(conditions), ["B2", "B3"])
    assert "error" in result


def test_compile_multiple_conditions():
    from tools.compiler import compile_protocol
    conditions = [
        {"base_media": "High Buffer Defined Media", "base_media_vol": 110,
         "yeast_extract": 14, "tryptone": 26, "na_l_glut": 10},
        {"base_media": "Semi-Defined Media", "base_media_vol": 125,
         "yeast_extract": 20, "tryptone": 14, "mops": 7},
    ]
    result = compile_protocol(json.dumps(conditions), ["B2", "B3"])
    assert result["n_transfers"] > 0
    assert len(result["well_summaries"]) == 2
    assert len(result["errors"]) == 0
