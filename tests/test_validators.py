"""Tests for validators — convergence check."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

def test_convergence_overlapping_ci():
    from tools.validators import check_convergence
    result = check_convergence(current_best_rate=1.62, current_best_se=0.05, previous_best_rate=1.60, previous_best_se=0.05)
    assert result["converged"] is True

def test_convergence_non_overlapping_ci():
    from tools.validators import check_convergence
    result = check_convergence(current_best_rate=2.0, current_best_se=0.05, previous_best_rate=1.0, previous_best_se=0.05)
    assert result["converged"] is False

def test_convergence_improvement_pct():
    from tools.validators import check_convergence
    result = check_convergence(current_best_rate=1.8, current_best_se=0.05, previous_best_rate=1.5, previous_best_se=0.05)
    assert result["improvement_pct"] > 0
    assert "CONTINUE" in result["recommendation"]

def test_convergence_stop_recommendation():
    from tools.validators import check_convergence
    result = check_convergence(current_best_rate=1.62, current_best_se=0.1, previous_best_rate=1.60, previous_best_se=0.1)
    assert "STOP" in result["recommendation"]
