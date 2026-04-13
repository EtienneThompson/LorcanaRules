import asyncio
from typing import Any

from models import CardResult
from search import CardsSearch

from .base import Tool


class LookupReferenceTool(Tool):
    """Tool that fetches a specific card by its reference ID supplied by the user."""

    @property
    def name(self) -> str:
        return "lookup_reference"

    @property
    def description(self) -> str:
        return (
            "Look up a specific Disney Lorcana card by its reference ID. "
            "Use this tool when the user's message contains a card reference in the "
            "format `card:<id>` (for example, `card:42`). "
            "Returns the full card data — name, abilities, stats, flavor text, and more — "
            "for that exact card so you can answer questions about it precisely."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "card_reference": {
                    "type": "string",
                    "description": (
                        "The card reference string exactly as it appears in the user's message, "
                        "in the format `card:<id>`, e.g. `card:42`."
                    ),
                },
            },
            "required": ["card_reference"],
        }

    async def execute(self, card_reference: str, **kwargs: Any) -> CardResult | None:
        """
        Parse the card ID from the reference string and fetch the card from the index.

        Args:
            card_reference: A string like ``card:42``.

        Returns:
            The matching CardResult, or None if the ID cannot be parsed or the card
            does not exist in the index.
        """
        try:
            card_id = int(card_reference.split(":", 1)[1])
        except (IndexError, ValueError):
            return None

        return await asyncio.to_thread(CardsSearch().get_by_id, card_id)
