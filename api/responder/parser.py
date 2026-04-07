from .models import TextOutput


class ResponderParser:
    """
    Processes a stream of tokens from the responder LLM and emits typed output
    objects.

    Each call to :meth:`feed` returns a list of output objects derived from the
    given token.  The list is empty when the parser is buffering (e.g. waiting
    to determine whether a token sequence forms a structured output type), and
    contains one or more items when output is ready to emit.

    Currently all tokens are emitted immediately as :class:`TextOutput`.  The
    buffer and list-return contract exist to support future output types
    (citations, card references) that require lookahead before they can be
    classified.
    """

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, token: str) -> list[TextOutput]:
        """
        Process a single token and return any output objects ready to emit.

        Args:
            token: A text chunk from the LLM stream.

        Returns:
            A list of output objects. Currently always a single
            :class:`TextOutput` wrapping the token.
        """
        return [TextOutput(text=token)]
