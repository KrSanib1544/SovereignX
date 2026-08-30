# backend/app/agent/tools/registry.py
"""
Central Tool Registry
Maintains the approved catalog of tools and provides formatted system prompt definitions.
"""

from typing import Dict, List, Optional
from backend.app.agent.tools.base import BaseTool, ToolDefinition
from backend.app.agent.tools.read_file import ReadFileTool
from backend.app.agent.tools.list_workspace import ListWorkspaceTool
from backend.app.agent.tools.search_knowledge import SearchKnowledgeTool
from backend.app.agent.tools.inspect_image import InspectImageTool
from backend.app.agent.tools.run_python import RunPythonTool
from backend.app.agent.tools.generate_docx import GenerateDocxTool


class ToolRegistry:
    """
    Catalog of registered agent tools with schema lookup and prompt formatting.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(ReadFileTool())
        self.register(ListWorkspaceTool())
        self.register(SearchKnowledgeTool())
        self.register(InspectImageTool())
        self.register(RunPythonTool())
        self.register(GenerateDocxTool())

    def register(self, tool: BaseTool) -> None:
        name = tool.definition.name
        self._tools[name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return [tool.definition for tool in self._tools.values()]

    def format_tools_for_prompt(self) -> str:
        """
        Render tools into structured JSON-compatible declarations for the model system prompt.
        """
        lines = []
        for tool in self._tools.values():
            defn = tool.definition
            lines.append(f"### Tool: `{defn.name}`")
            lines.append(f"- **Description**: {defn.description}")
            lines.append(f"- **Risk Level**: {defn.risk_level.value}")
            lines.append(f"- **Requires Approval**: {defn.requires_human_approval}")
            lines.append(f"- **Input Schema**: `{defn.input_schema.model_json_schema()}`")
            lines.append("")
        return "\n".join(lines)
