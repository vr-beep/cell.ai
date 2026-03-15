"""Tests for Elnora client — tests CLI wrapper structure (no live calls in CI)."""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_elnora_design_builds_correct_prompt():
    """Verify the prompt template is well-formed."""
    from tools.elnora_client import elnora_design

    with patch("tools.elnora_client._create_task") as mock_create, \
         patch("tools.elnora_client._get_messages") as mock_msgs:
        mock_create.return_value = {"id": "fake-uuid"}
        mock_msgs.return_value = [
            {"role": "assistant", "content": "Proposed conditions: ..."}
        ]

        result = elnora_design(
            results_summary="| HB-1 | 1.616 |",
            round_number=2,
            n_conditions=10,
        )

        assert result["task_id"] == "fake-uuid"
        assert result["round"] == 2
        assert len(result["elnora_response"]) > 0

        # Verify prompt contains key elements
        call_args = mock_create.call_args
        prompt = call_args[0][1]  # second positional arg = message
        assert "V. natriegens" in prompt
        assert "10 conditions" in prompt
        assert "Round 2" in prompt


def test_elnora_validate_builds_correct_prompt():
    from tools.elnora_client import elnora_validate

    with patch("tools.elnora_client._create_task") as mock_create, \
         patch("tools.elnora_client._get_messages") as mock_msgs:
        mock_create.return_value = {"id": "fake-uuid-2"}
        mock_msgs.return_value = [
            {"role": "assistant", "content": "ALL CLEAR"}
        ]

        result = elnora_validate("| HB-R2-1 | YE 7 | Tryp 15 | Glut 60 |")

        assert result["task_id"] == "fake-uuid-2"
        assert "ALL CLEAR" in result["validation_result"]
