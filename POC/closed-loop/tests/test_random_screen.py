"""Tests for random screening tool."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_lhs_returns_correct_count():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=10)
    assert result["n_conditions"] == 10
    assert result["method"] == "latin_hypercube"


def test_lhs_conditions_have_valid_volumes():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=5)
    for cond in result["conditions"]:
        assert cond["total"] == 200
        assert cond["cells"] == 20
        assert cond["water"] >= 0


def test_lhs_respects_fixed_base_media():
    from tools.random_screen import latin_hypercube_screen
    result = latin_hypercube_screen(n_conditions=5, base_media="Semi-Defined Media")
    for cond in result["conditions"]:
        assert cond["base_media"] == "Semi-Defined Media"
