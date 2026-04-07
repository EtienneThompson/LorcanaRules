from dataclasses import dataclass


@dataclass
class TextOutput:
    """A plain-text token or chunk intended for direct display to the user."""

    text: str


# Future output types — not yet implemented:
#
# @dataclass
# class CitationOutput:
#     """A reference to a specific rule. The orchestrator resolves this to rule text."""
#     rule_id: str
#
# @dataclass
# class CardOutput:
#     """A reference to a specific card. The orchestrator resolves this to card data."""
#     card_id: int
