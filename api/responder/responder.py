from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from llm import AzureOpenAIClient
from models import CardResult, RuleResult
from prompts import PromptFormatter

from .models import TextOutput
from .parser import ResponderParser

if TYPE_CHECKING:
    from tools import ToolResult

logger = logging.getLogger(__name__)


def _build_context(tool_results: list[ToolResult]) -> str:
    """
    Format a list of tool results into a readable context string for the LLM.

    Cards and rules are rendered in separate sections so the model can easily
    distinguish between them.
    """
    cards: list[CardResult] = []
    rules: list[RuleResult] = []

    for tr in tool_results:
        for item in tr.result:
            if isinstance(item, CardResult):
                cards.append(item)
            elif isinstance(item, RuleResult):
                rules.append(item)

    sections: list[str] = []

    if cards:
        lines = ["### Cards"]
        for card in cards:
            lines.append(f"**{card.fullName}** (score: {card.score:.4f})")
            lines.append(card.completeCardText)
        sections.append("\n".join(lines))

    if rules:
        lines = ["### Rules"]
        for rule in rules:
            section_path = " > ".join(rule.sections) if rule.sections else ""
            header = f"**Rule {rule.rule_id}**" + (f" — {section_path}" if section_path else "")
            lines.append(f"{header} (score: {rule.score:.4f})")
            lines.append(rule.rule_text)
        sections.append("\n".join(lines))

    return "\n\n".join(sections)


class Responder:
    """
    Generates a streamed natural-language response from the user's query and
    tool results.

    The responder renders a system prompt containing the retrieved context,
    sends it to the LLM alongside the user query, and yields typed output
    objects parsed from the response stream.

    Usage::

        responder = Responder()
        async for output in responder.respond(query, tool_results):
            if isinstance(output, TextOutput):
                print(output.text, end="", flush=True)
    """

    def __init__(self) -> None:
        self._formatter = PromptFormatter()
        self._llm = AzureOpenAIClient()
        self._parser = ResponderParser()

    async def respond(
        self,
        query: str,
        tool_results: list[ToolResult],
    ) -> AsyncGenerator[TextOutput, None]:
        """
        Stream a response for the given query and tool results.

        Args:
            query:        The user's original question.
            tool_results: Results returned by the tool executor.

        Yields:
            Typed output objects from the response stream. Currently always
            :class:`TextOutput`.
        """
        context = _build_context(tool_results)
        system_prompt = self._formatter.render("responder", "system.j2", context=context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        logger.info("Responder streaming for query: %r", query)

        async for chunk in self._llm.stream(messages=messages):
            for output in self._parser.feed(chunk):
                yield output

        logger.info("Responder finished.")
