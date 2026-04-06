import asyncio
from typing import Any

from models import RuleResult
from search import RulesSearch

from .base import Tool


class SearchRulesTool(Tool):
    """Tool that searches the Lorcana rules Azure AI Search index."""

    @property
    def name(self) -> str:
        return "search_rules"

    @property
    def description(self) -> str:
        return (
            "Search the Disney Lorcana comprehensive rules document using a natural-language "
            "query. Returns the most relevant rules sections, including their rule ID, "
            "section hierarchy, and full rule text. Use this tool when the user asks about "
            "game rules, mechanics, interactions, or official rulings."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural-language search query used for vector search against "
                        "the rules index. Be specific — include keywords, rule concepts, "
                        "or mechanic names relevant to the user's question."
                    ),
                },
                "top": {
                    "type": "integer",
                    "description": "Maximum number of rules to return. Defaults to 5.",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, top: int = 5, **kwargs: Any) -> list[RuleResult]:
        """
        Search the rules index and return matching RuleResult objects.

        Args:
            query: The search query string.
            top:   Maximum number of results to return.

        Returns:
            A list of matching RuleResult objects.
        """
        return await asyncio.to_thread(RulesSearch().search, query=query, top=top)
