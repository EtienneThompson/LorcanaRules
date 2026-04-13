from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Iterable
from typing import TYPE_CHECKING, Any

from llm import AzureOpenAIClient
from models import CardResult, RuleResult
from prompts import PromptFormatter

from .models import CardOutput, CitationOutput, TextOutput
from .parser import ResponderOutput, ResponderParser

if TYPE_CHECKING:
    from tools import ToolResult

logger = logging.getLogger(__name__)


def _iter_result(result: Any) -> Iterable[Any]:
    """
    Normalise a tool result value into an iterable of items.

    Tools may return a list, a single object, or None:
      - list   → iterate as-is, skipping None entries
      - single → wrap in a one-element list
      - None   → empty iterable (tool returned no data)
    """
    if result is None:
        return ()
    if isinstance(result, list):
        return (item for item in result if item is not None)
    return (result,)


def _build_rules_map(tool_results: list[ToolResult]) -> dict[str, str]:
    """Return a mapping of rule_id → rule_text from the tool results."""
    rules: dict[str, str] = {}
    for tr in tool_results:
        for item in _iter_result(tr.result):
            if isinstance(item, RuleResult):
                rules[item.rule_id] = item.rule_text
    return rules


def _build_cards_map(
    tool_results: list[ToolResult],
) -> tuple[dict[int, tuple[str, str]], dict[str, tuple[int, str, str]]]:
    """
    Return two lookups built from card tool results:
      - id_map:   card_id (int)  → (full_name, image_url)
      - name_map: normalised name → (card_id, full_name, image_url)

    The name map is used as a fallback when the model emits [[Card Name]]
    instead of [[card_id]].
    """
    id_map: dict[int, tuple[str, str]] = {}
    name_map: dict[str, tuple[int, str, str]] = {}
    for tr in tool_results:
        for item in _iter_result(tr.result):
            if isinstance(item, CardResult):
                entry = (item.fullName, item.images.full)
                id_map[item.id] = entry
                name_map[item.fullName.lower()] = (item.id, item.fullName, item.images.full)
    return id_map, name_map


def _build_context(tool_results: list[ToolResult]) -> str:
    """
    Format a list of tool results into a readable context string for the LLM.

    Cards and rules are rendered in separate sections so the model can easily
    distinguish between them.
    """
    cards: list[CardResult] = []
    rules: list[RuleResult] = []

    for tr in tool_results:
        for item in _iter_result(tr.result):
            if isinstance(item, CardResult):
                cards.append(item)
            elif isinstance(item, RuleResult):
                rules.append(item)

    sections: list[str] = []

    if cards:
        lines = ["### Cards"]
        for card in cards:
            lines.append(f"**{card.fullName}** (card_id: {card.id}, score: {card.score:.4f})")
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
            elif isinstance(output, CitationOutput):
                print(f"[{output.number}] Rule {output.rule_id}")
    """

    def __init__(self) -> None:
        self._formatter = PromptFormatter()
        self._llm = AzureOpenAIClient()

    async def respond(
        self,
        query: str,
        tool_results: list[ToolResult],
    ) -> AsyncGenerator[ResponderOutput, None]:
        """
        Stream a response for the given query and tool results.

        A fresh :class:`ResponderParser` is created per call so that citation
        counters reset correctly across requests.

        Args:
            query:        The user's original question.
            tool_results: Results returned by the tool executor.

        Yields:
            :class:`TextOutput` and :class:`CitationOutput` objects in the
            order they are generated.
        """
        rules_map = _build_rules_map(tool_results)
        cards_id_map, cards_name_map = _build_cards_map(tool_results)
        parser = ResponderParser(rules=rules_map, cards=cards_id_map, cards_by_name=cards_name_map)

        context = _build_context(tool_results)
        system_prompt = self._formatter.render("responder", "system.j2", context=context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        logger.info("Responder streaming for query: %r", query)

        async for chunk in self._llm.stream(messages=messages):
            for output in parser.feed(chunk):
                yield output

        for output in parser.flush():
            yield output

        logger.info("Responder finished.")
