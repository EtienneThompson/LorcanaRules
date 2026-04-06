import os

from azure.search.documents import SearchClient
from azure.search.documents.models import SearchMode, VectorizableTextQuery

from models import CardResult

from .client import create_search_client

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
