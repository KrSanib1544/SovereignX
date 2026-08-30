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
