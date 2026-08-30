# backend/tests/unit/test_react_agent.py
"""
Unit Tests for ReAct Agent
Validates reasoning output parsing, thinking tag privacy filtering, loop detection, and state machine bounds.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.app.agent.core.loop_detector import LoopDetector
from backend.app.agent.core.react_agent import ReActAgent
from backend.app.agent.core.state import AgentState
from backend.app.agent.tools.registry import ToolRegistry
from backend.app.models.types import GenerationResponse


def test_private_reasoning_filter_and_json_parsing():
    agent = ReActAgent()
    raw_model_output = """<think>
Internal private reasoning chain that must never be exposed to the user.
Step 1: check files.
Step 2: formulate query.
</think>
```json
{
  "thought": "I need to inspect the workspace files.",
  "tool": "list_workspace",
  "arguments": {
    "subdirectory": "artifacts"
  }
}
```"""

    thought, tool, args, final_ans = agent._parse_model_output(raw_model_output)

    assert "Internal private reasoning" not in thought
    assert thought == "I need to inspect the workspace files."
    assert tool == "list_workspace"
    assert args == {"subdirectory": "artifacts"}
    assert final_ans is None


def test_final_answer_parsing():
    agent = ReActAgent()
    raw_output = """```json
{
  "thought": "All tasks are complete.",
  "final_answer": "The pump casing wall thickness is 3.42mm and requires immediate replacement."
}
```"""
    thought, tool, args, final_ans = agent._parse_model_output(raw_output)
    assert tool is None
    assert "immediate replacement" in final_ans


def test_loop_detector_catches_repeated_actions():
    detector = LoopDetector(max_consecutive_repeats=3)

    # 1st call
    loop, _ = detector.record_action("read_file", {"filename": "data.csv"})
    assert loop is False

    # 2nd call
    loop, _ = detector.record_action("read_file", {"filename": "data.csv"})
    assert loop is False

    # 3rd identical call
    loop, reason = detector.record_action("read_file", {"filename": "data.csv"})
    assert loop is True
    assert "Infinite loop detected" in reason


@pytest.mark.asyncio
async def test_agent_completes_in_single_step():
    mock_router = AsyncMock()
    mock_router.generate.return_value = GenerationResponse(
        model="qwen3:4b",
        content='{"thought": "Done", "final_answer": "Compliance confirmed."}',
        total_duration_ms=120.0
    )

    agent = ReActAgent(model_router=mock_router)
    result = await agent.execute_task(
        workspace_id="test-ws-01",
        prompt="Verify compliance"
    )

    assert result.state == AgentState.COMPLETED
    assert result.final_answer == "Compliance confirmed."
    assert result.total_steps == 1


def test_parser_clean_json():
    agent = ReActAgent()
    raw = '{"thought": "Direct query", "tool": "search_vault", "arguments": {"query": "wall thickness"}}'
    thought, tool, args, fa = agent._parse_model_output(raw)
    assert thought == "Direct query"
    assert tool == "search_vault"
    assert args == {"query": "wall thickness"}
    assert fa is None


def test_parser_fenced_json():
    agent = ReActAgent()
    raw = """Here is my decision:
```json
{
  "thought": "I will run python calculations",
  "tool": "run_python",
  "arguments": {"script_code": "print(42)"}
}
```"""
    thought, tool, args, fa = agent._parse_model_output(raw)
    assert thought == "I will run python calculations"
    assert tool == "run_python"
    assert args == {"script_code": "print(42)"}
    assert fa is None


def test_parser_conversational_text_followed_by_json():
    agent = ReActAgent()
    raw = """Based on the preliminary analysis, I need to execute a calculation.
Sure, let me check the dataset:
{"thought": "Calculating thinning rate", "tool": "run_python", "arguments": {"script_code": "import numpy as np"}}
Hope this helps!"""
    thought, tool, args, fa = agent._parse_model_output(raw)
    assert thought == "Calculating thinning rate"
    assert tool == "run_python"
    assert args == {"script_code": "import numpy as np"}
    assert fa is None


def test_parser_malformed_json_fallback():
    agent = ReActAgent()
    raw = """I cannot parse this JSON properly: {thought: incomplete, "tool": ...
However, based on my analysis, the casing is cracked and requires immediate shutdown."""
    thought, tool, args, fa = agent._parse_model_output(raw)
    assert tool is None
    assert fa is not None
    assert "casing is cracked" in fa


def test_parser_multiple_json_fragments():
    agent = ReActAgent()
    raw = """Previous state was {"status": "old"}.
Now I choose the next action:
{"thought": "Inspecting visual image", "tool": "inspect_image", "arguments": {"image_filename": "crack.jpg"}}"""
    thought, tool, args, fa = agent._parse_model_output(raw)
    assert thought == "Inspecting visual image"
    assert tool == "inspect_image"
    assert args == {"image_filename": "crack.jpg"}
    assert fa is None
