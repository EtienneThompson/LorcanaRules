from dataclasses import dataclass


@dataclass
class TextOutput:
    """A plain-text token or chunk intended for direct display to the user."""

    text: str


@dataclass
class CitationOutput:
    """
    A reference to a specific rule emitted when the LLM generates {{rule_id}}.

    Attributes:
        rule_id:  The rule identifier as it appears in the rules index (e.g. "4.3.1").
        rule_text: The full text of the rule, looked up from the tool results.
        number:   1-based citation counter for this response, used to render the
                  inline badge (e.g. ¹, ², …).
    """

    rule_id: str
    rule_text: str
    number: int


@dataclass
class CardOutput:
    """
    A reference to a specific card emitted when the LLM generates [[card_id]].

    Attributes:
        card_id:   The numeric card ID as it appears in the cards index.
        full_name: The card's full display name (e.g. "Elsa - Snow Queen").
        image_url: URL of the card's full artwork image.
    """

    card_id: int
    full_name: str
    image_url: str
