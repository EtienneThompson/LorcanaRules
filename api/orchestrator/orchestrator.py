import asyncio
import logging
from collections.abc import AsyncGenerator

from planner import Planner
from responder import Responder, TextOutput
from tools import ToolExecutor, ToolRegistry, ToolResult

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Controls the end-to-end RAG pipeline: plan → execute → respond.

    The planner streams tool calls as soon as each one is generated; each call
    is immediately dispatched as an async task so tool execution overlaps with
    the planner still generating subsequent calls.  Once all tool results are
    gathered, they are passed to the responder which streams back a typed
    response.

    Usage::

        orchestrator = Orchestrator(registry)
        async for output in orchestrator.orchestrate("What does Elsa cost?"):
            if isinstance(output, TextOutput):
                print(output.text, end="", flush=True)
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._planner = Planner(tools=registry.all())
        self._executor = ToolExecutor(registry)
        self._responder = Responder()

    async def orchestrate(self, query: str) -> AsyncGenerator[TextOutput, None]:
        """
        Run the full pipeline for the given query and stream back typed output.

        Args:
            query: The user's natural-language question.

        Yields:
            Typed output objects from the responder stream.
        """
        logger.info("Orchestrator starting for query: %r", query)

        tasks = []
        async for tool_call in self._planner.plan(query):
            tasks.append(asyncio.create_task(self._executor.execute(tool_call)))

        tool_results: list[ToolResult] = list(await asyncio.gather(*tasks))
        logger.info("Orchestrator gathered %d tool result(s)", len(tool_results))

        async for output in self._responder.respond(query, tool_results):
            yield output

        logger.info("Orchestrator finished.")
