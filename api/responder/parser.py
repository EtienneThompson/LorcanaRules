from .models import CitationOutput, TextOutput

ResponderOutput = TextOutput | CitationOutput


class ResponderParser:
    """
    Processes a stream of tokens from the responder LLM and emits typed output
    objects.

    Each call to :meth:`feed` returns a list of output objects derived from the
    given token.  The list is empty when the parser is buffering (e.g. waiting
    to accumulate a full ``{{rule_id}}`` citation), and contains one or more
    items when output is ready to emit.

    When the LLM emits ``{{rule_id}}``, the surrounding text is emitted as
    :class:`TextOutput` chunks and the citation itself becomes a
    :class:`CitationOutput` with the rule text looked up from the supplied
    rules map.  Unknown rule IDs are emitted with an empty ``rule_text``.

    Call :meth:`flush` after the stream ends to emit any content that is still
    buffered (e.g. an unclosed ``{{`` that the model never closed).
    """

    def __init__(self, rules: dict[str, str]) -> None:
        """
        Args:
            rules: Mapping of rule_id → rule_text built from the current
                   request's tool results.
        """
        self._rules = rules
        self._buffer = ""
        self._in_citation = False
        self._citation_counter = 0

    def feed(self, token: str) -> list[ResponderOutput]:
        """
        Process a single token and return any output objects ready to emit.

        Args:
            token: A text chunk from the LLM stream.

        Returns:
            A (possibly empty) list of :class:`TextOutput` and/or
            :class:`CitationOutput` objects.
        """
        outputs: list[ResponderOutput] = []
        self._buffer += token

        while self._buffer:
            if self._in_citation:
                close_idx = self._buffer.find('}}')
                if close_idx != -1:
                    rule_id = self._buffer[:close_idx].strip()
                    self._buffer = self._buffer[close_idx + 2:]
                    self._in_citation = False
                    self._citation_counter += 1
                    outputs.append(CitationOutput(
                        rule_id=rule_id,
                        rule_text=self._rules.get(rule_id, ""),
                        number=self._citation_counter,
                    ))
                else:
                    break  # wait for closing }}
            else:
                open_idx = self._buffer.find('{{')
                if open_idx != -1:
                    if open_idx > 0:
                        outputs.append(TextOutput(text=self._buffer[:open_idx]))
                    self._buffer = self._buffer[open_idx + 2:]
                    self._in_citation = True
                else:
                    # No {{ found, but a trailing `{` might be the start of one.
                    if self._buffer.endswith('{'):
                        if len(self._buffer) > 1:
                            outputs.append(TextOutput(text=self._buffer[:-1]))
                        self._buffer = '{'
                    else:
                        outputs.append(TextOutput(text=self._buffer))
                        self._buffer = ''
                    break

        return outputs

    def flush(self) -> list[ResponderOutput]:
        """
        Emit any content still held in the buffer at end-of-stream.

        If the model never closed a ``{{`` block, the raw ``{{…`` text is
        emitted as :class:`TextOutput` so nothing is silently dropped.
        """
        if not self._buffer:
            return []
        prefix = '{{' if self._in_citation else ''
        text = prefix + self._buffer
        self._buffer = ''
        self._in_citation = False
        return [TextOutput(text=text)]
