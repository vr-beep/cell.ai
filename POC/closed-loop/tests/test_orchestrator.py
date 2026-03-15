"""Tests for orchestrator — tool dispatch and structure."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

def test_get_tools_returns_valid_schema():
    from orchestrator import get_tools
    tools = get_tools()
    assert len(tools) >= 7
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool

def test_execute_tool_analyze():
    from orchestrator import execute_tool
    result_json = execute_tool("analyze_results", {"current_round_csv": "data/PLT1RLOSUISCDIHOFWDWTLWCUPCOLQ_growth.csv"})
    result = json.loads(result_json)
    assert "best_growth_rate" in result
    assert result["best_growth_rate"] > 1.5

def test_execute_tool_convergence():
    from orchestrator import execute_tool
    result_json = execute_tool("check_convergence", {"current_best_rate": 1.62, "current_best_se": 0.05, "previous_best_rate": 1.60, "previous_best_se": 0.05})
    result = json.loads(result_json)
    assert "converged" in result

def test_execute_unknown_tool():
    from orchestrator import execute_tool
    result_json = execute_tool("nonexistent_tool", {})
    result = json.loads(result_json)
    assert "error" in result
