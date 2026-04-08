from .models import CardOutput, CitationOutput, TextOutput

ResponderOutput = TextOutput | CitationOutput | CardOutput

# Parser states
_STATE_TEXT = "text"
_STATE_CITATION = "citation"   # inside {{ … }}
_STATE_CARD = "card"           # inside [[ … ]]


class ResponderParser:
    """
    Processes a stream of tokens from the responder LLM and emits typed output
    objects.

    Recognised inline markers:
      ``{{rule_id}}``  → :class:`CitationOutput`
      ``[[card_id]]``  → :class:`CardOutput`

    Everything else passes through as :class:`TextOutput`.

    Call :meth:`flush` after the stream ends to emit any content still held in
    the buffer (e.g. an unclosed marker the model never closed).
    """

    def __init__(
        self,
        rules: dict[str, str],
        cards: dict[int, tuple[str, str]],
        cards_by_name: dict[str, tuple[int, str, str]] | None = None,
    ) -> None:
        """
        Args:
            rules:          Mapping of rule_id → rule_text.
            cards:          Mapping of card_id (int) → (full_name, image_url).
            cards_by_name:  Optional mapping of normalised name →
                            (card_id, full_name, image_url), used as a fallback
                            when the model emits [[Card Name]] instead of [[id]].
        """
        self._rules = rules
        self._cards = cards
        self._cards_by_name = cards_by_name or {}
        self._buffer = ""
        self._state = _STATE_TEXT
        self._citation_counter = 0

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def feed(self, token: str) -> list[ResponderOutput]:
        """
        Process a single token and return any output objects ready to emit.

        Returns:
            A (possibly empty) list of output objects.
        """
        outputs: list[ResponderOutput] = []
        self._buffer += token

        while self._buffer:
            if self._state == _STATE_CITATION:
                outputs.extend(self._scan_close('}}', self._emit_citation))
                break
            elif self._state == _STATE_CARD:
                outputs.extend(self._scan_close(']]', self._emit_card))
                break
            else:
                # In text state — look for the earliest opening marker.
                cite_idx = self._buffer.find('{{')
                card_idx = self._buffer.find('[[')

                # Determine which marker comes first.
                if cite_idx == -1 and card_idx == -1:
                    # No marker found; might end with a partial opener.
                    if self._buffer.endswith('{') or self._buffer.endswith('['):
                        if len(self._buffer) > 1:
                            outputs.append(TextOutput(text=self._buffer[:-1]))
                        self._buffer = self._buffer[-1]
                    else:
                        outputs.append(TextOutput(text=self._buffer))
                        self._buffer = ''
                    break

                # Pick the closer opening.
                if cite_idx == -1:
                    open_idx, open_len, new_state = card_idx, 2, _STATE_CARD
                elif card_idx == -1:
                    open_idx, open_len, new_state = cite_idx, 2, _STATE_CITATION
                else:
                    if cite_idx <= card_idx:
                        open_idx, open_len, new_state = cite_idx, 2, _STATE_CITATION
                    else:
                        open_idx, open_len, new_state = card_idx, 2, _STATE_CARD

                if open_idx > 0:
                    outputs.append(TextOutput(text=self._buffer[:open_idx]))
                self._buffer = self._buffer[open_idx + open_len:]
                self._state = new_state

        return outputs

    def flush(self) -> list[ResponderOutput]:
        """Emit any content still in the buffer at end-of-stream."""
        if not self._buffer:
            return []
        if self._state == _STATE_CITATION:
            text = '{{' + self._buffer
        elif self._state == _STATE_CARD:
            text = '[[' + self._buffer
        else:
            text = self._buffer
        self._buffer = ''
        self._state = _STATE_TEXT
        return [TextOutput(text=text)]

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _scan_close(
        self,
        close: str,
        emitter,
    ) -> list[ResponderOutput]:
        """Wait for `close` in the buffer then call `emitter` with the content."""
        idx = self._buffer.find(close)
        if idx == -1:
            return []  # still waiting
        content = self._buffer[:idx].strip()
        self._buffer = self._buffer[idx + len(close):]
        self._state = _STATE_TEXT
        return emitter(content)

    def _emit_citation(self, rule_id: str) -> list[ResponderOutput]:
        self._citation_counter += 1
        return [CitationOutput(
            rule_id=rule_id,
            rule_text=self._rules.get(rule_id, ""),
            number=self._citation_counter,
        )]

    def _emit_card(self, raw_id: str) -> list[ResponderOutput]:
        # Try numeric ID first.
        try:
            card_id = int(raw_id)
            entry = self._cards.get(card_id)
            if entry:
                full_name, image_url = entry
                return [CardOutput(card_id=card_id, full_name=full_name, image_url=image_url)]
        except ValueError:
            pass

        # Fall back to name lookup (model used [[Card Name]] instead of [[id]]).
        name_entry = self._cards_by_name.get(raw_id.lower())
        if name_entry:
            card_id, full_name, image_url = name_entry
            return [CardOutput(card_id=card_id, full_name=full_name, image_url=image_url)]

        return [TextOutput(text=f"[[{raw_id}]]")]
