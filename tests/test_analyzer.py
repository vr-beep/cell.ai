"""Tests for growth data analyzer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

DATA_DIR = Path(__file__).parent.parent / "data"
GROWTH_CSV = str(DATA_DIR / "PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv")


def test_analyze_returns_ranked_conditions():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert "ranked_conditions" in result
    assert result["n_conditions"] == 10
    assert result["best_growth_rate"] > 1.5


def test_analyze_best_condition_is_hb1():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert "HB-1" in result["best_condition"]


def test_analyze_computes_se():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV)
    assert result["best_se"] > 0
    assert result["best_se"] < 1.0


def test_analyze_convergence_false_on_first_round():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV, previous_best_rate=0.0)
    assert result["converged"] is False


def test_analyze_convergence_true_when_same():
    from tools.analyzer import analyze_results
    result = analyze_results(GROWTH_CSV, previous_best_rate=1.616)
    assert result["converged"] is True


def test_analyze_missing_file():
    from tools.analyzer import analyze_results
    result = analyze_results("/nonexistent/file.csv")
    assert "error" in result
