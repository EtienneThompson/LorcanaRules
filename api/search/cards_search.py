import logging
import os

from azure.search.documents import SearchClient
from azure.search.documents.models import SearchMode, VectorizableTextQuery

from models import CardResult

from .client import create_search_client

logger = logging.getLogger(__name__)

_VECTOR_FIELD = "text_vector"
_MIN_SCORE = 0.0


class CardsSearch:
    """Search logic for the cards Azure AI Search index."""

    def __init__(self) -> None:
        index_name = os.environ["AZURE_SEARCH_CARDS_INDEX"]
        self._client: SearchClient = create_search_client(index_name)

    def search(
        self,
        query: str,
        top: int = 5,
    ) -> list[CardResult]:
        """
        Hybrid search (keyword + vector) the cards index with the given query.

        Args:
            query: The search query string.
            top:   Maximum number of results to return.

        Returns:
            A list of matching CardResult objects with score >= _MIN_SCORE.
        """
        vector_query = VectorizableTextQuery(
            text=query,
            k_nearest_neighbors=50,
            fields=_VECTOR_FIELD,
        )
        results = self._client.search(
            search_text=query,
            search_mode=SearchMode.ALL,
            vector_queries=[vector_query],
            top=top,
        )
        return [
            card
            for result in results
            if (card := CardResult.model_validate(dict(result))).score >= _MIN_SCORE
        ]

    def get_by_id(self, card_id: int) -> CardResult | None:
        """
        Fetch a single card document from the index by its numeric ID.

        Uses a filtered search on the ``id`` field rather than a point-lookup
        because the index key is an internal chunk identifier, not the card id.

        Args:
            card_id: The integer ID of the card to retrieve.

        Returns:
            A CardResult if the document exists, otherwise None.
        """
        try:
            results = self._client.search(
                search_text="*",
                filter=f"id eq {card_id}",
                top=1,
            )
            for result in results:
                return CardResult.model_validate(dict(result))
            logger.warning("get_by_id: no document found for card_id=%d", card_id)
            return None
        except Exception:
            logger.exception("get_by_id failed for card_id=%d", card_id)
            return None

    def search_by_name_prefix(self, prefix: str, top: int = 10) -> list[CardResult]:
        """
        Return cards whose fullName starts with the given prefix (case-insensitive).

        Uses a wildcard keyword search then filters client-side so the result set
        is always a strict startswith match regardless of index configuration.

        Args:
            prefix: The name prefix to match.
            top:    Maximum number of results to return.

        Returns:
            A list of matching CardResult objects.
        """
        escaped = prefix.replace("'", "\\'")
        results = self._client.search(
            search_text=f"{escaped}*",
            search_mode=SearchMode.ANY,
            top=top * 4,  # over-fetch so client-side filter has enough candidates
        )
        prefix_lower = prefix.lower()
        matches = []
        seen_ids: set[int] = set()
        for result in results:
            card = CardResult.model_validate(dict(result))
            if card.id in seen_ids:
                continue
            if card.fullName.lower().startswith(prefix_lower):
                seen_ids.add(card.id)
                matches.append(card)
                if len(matches) >= top:
                    break
        return matches
