import asyncio
import logging

from planner import Planner
from tools import ToolExecutor, ToolRegistry, ToolResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Controls the end-to-end RAG pipeline: plan → execute → (respond).

    The planner streams tool calls as soon as each one is generated; each call
    is immediately dispatched as an async task so tool execution overlaps with
    the planner still generating subsequent calls.  All tasks are awaited before
    the results are returned.

    Usage::

        orchestrator = Orchestrator(registry)
        results = await orchestrator.orchestrate("What does Elsa cost?")
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._planner = Planner(tools=registry.all())
        self._executor = ToolExecutor(registry)

    async def orchestrate(self, query: str) -> list[ToolResult]:
        """
        Run the full pipeline for the given query and return tool results.

        Args:
            query: The user's natural-language question.

        Returns:
            A list of :class:`ToolResult` objects, one per tool call emitted
            by the planner, in the order they were dispatched.
        """
        logger.info("Orchestrator starting for query: %r", query)

        tasks = []
        async for tool_call in self._planner.plan(query):
            tasks.append(asyncio.create_task(self._executor.execute(tool_call)))

        results = list(await asyncio.gather(*tasks))
        logger.info("Orchestrator finished with %d result(s)", len(results))
        return results
