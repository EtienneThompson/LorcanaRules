from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .registry import ToolRegistry

if TYPE_CHECKING:
    from planner import ToolCall

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """The result of executing a single tool call."""

    tool_call: ToolCall
    result: Any


class ToolExecutor:
    """
    Executes a :class:`ToolCall` by looking up the tool in the registry and
    calling its ``execute`` method with the parsed arguments.

    Usage::

        executor = ToolExecutor(registry)
        result = await executor.execute(tool_call)
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a single tool call and return its result.

        Args:
            tool_call: The :class:`ToolCall` emitted by the planner.

        Returns:
            A :class:`ToolResult` pairing the original call with its output.

        Raises:
            KeyError: if the tool name is not registered.
        """
        tool = self._registry.get(tool_call.name)
        logger.info("Executing tool %r with args %r", tool_call.name, tool_call.arguments)
        result = await tool.execute(**tool_call.arguments)
        logger.info("Tool %r returned %d result(s)", tool_call.name, len(result) if hasattr(result, "__len__") else 1)
        return ToolResult(tool_call=tool_call, result=result)
