import asyncio
from typing import Any

from models import CardResult
from search import CardsSearch

from .base import Tool


class SearchCardsTool(Tool):
    """Tool that searches the Lorcana cards Azure AI Search index."""

    @property
    def name(self) -> str:
        return "search_cards"

    @property
    def description(self) -> str:
        return (
            "Search the Disney Lorcana card database using a natural-language query. "
            "Returns the most relevant cards, including their name, type, cost, color, "
            "abilities, flavor text, and stats. Use this tool when the user asks about "
            "specific cards, card abilities, or wants to find cards matching certain criteria."
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
                        "the cards index. Be specific — include card names, colors, "
                        "abilities, or keywords relevant to the user's question."
                    ),
                },
                "top": {
                    "type": "integer",
                    "description": "Maximum number of cards to return. Defaults to 5.",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str, top: int = 5, **kwargs: Any) -> list[CardResult]:
        """
        Search the cards index and return matching CardResult objects.

        Args:
            query: The search query string.
            top:   Maximum number of results to return.

        Returns:
            A list of matching CardResult objects.
        """
        return await asyncio.to_thread(CardsSearch().search, query=query, top=top)
