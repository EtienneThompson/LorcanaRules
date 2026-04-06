import logging
from collections.abc import AsyncGenerator

from llm import AzureOpenAIClient
from prompts import PromptFormatter
from tools import Tool

from .models import ToolCall
from .parser import parse_tool_call

logger = logging.getLogger(__name__)


def _build_tools_context(tools: list[Tool]) -> list[dict]:
    """
    Convert a list of Tool objects into a template-friendly list of dicts.

    Jinja2 templates receive plain dicts rather than live Python objects so
    that templates stay decoupled from the tool class hierarchy.
    """
    result = []
    for tool in tools:
        schema = tool.parameters
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})

        params = []
        for param_name, param_schema in properties.items():
            params.append(
                {
                    "name": param_name,
                    "type": param_schema.get("type", "string"),
                    "description": param_schema.get("description", ""),
                    "required": param_name in required,
                    "default": param_schema.get("default"),
                }
            )

        result.append(
            {
                "name": tool.name,
                "description": tool.description,
                "params": params,
            }
        )
    return result


class Planner:
    """
    Decides which tools to call for a given user query.

    The planner renders its system prompt via :class:`PromptFormatter`, sends
    the prompt + user query to the LLM, and streams back :class:`ToolCall`
    objects as soon as each complete line is received.  This means tools can
    be dispatched in parallel — the first tool call is yielded the moment its
    line is fully generated, without waiting for subsequent tool calls to
    finish streaming.

    Usage::

        tools = [SearchCardsTool(), SearchRulesTool()]
        planner = Planner(tools=tools)

        async for tool_call in planner.plan("What does Elsa cost and can she quest?"):
            results = await dispatch(tool_call)
    """

    def __init__(
        self,
        tools: list[Tool],
        temperature: float = 0.0,
    ) -> None:
        """
        Args:
            tools:       The tools the planner may choose from.
            temperature: Sampling temperature for the planner LLM call.
                         Defaults to 0.0 for deterministic output.
        """
        self._tools = tools
        self._temperature = temperature
        self._formatter = PromptFormatter()
        self._llm = AzureOpenAIClient()

    async def plan(self, query: str) -> AsyncGenerator[ToolCall, None]:
        """
        Stream tool calls for the given user query.

        Internally streams the LLM response token-by-token, buffers until a
        newline is received, then immediately parses and yields each completed
        line as a :class:`ToolCall`.  Lines that do not match the expected
        format (blank lines, stray prose) are silently skipped.

        Args:
            query: The user's natural-language question.

        Yields:
            :class:`ToolCall` objects in the order the planner generates them.
        """
        tools_context = _build_tools_context(self._tools)
        system_prompt = self._formatter.render(
            "planner", "system.j2", tools=tools_context
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        logger.info("Planner streaming for query: %r", query)

        buffer = ""
        async for chunk in self._llm.stream(messages=messages, temperature=self._temperature):
            buffer += chunk

            # Yield any complete lines immediately.
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                tool_call = parse_tool_call(line)
                if tool_call is not None:
                    logger.info("Planner emitted: %r", tool_call)
                    yield tool_call

        # Handle the final line if the model didn't end with a newline.
        if buffer.strip():
            tool_call = parse_tool_call(buffer)
            if tool_call is not None:
                logger.info("Planner emitted: %r", tool_call)
                yield tool_call

        logger.info("Planner finished.")
