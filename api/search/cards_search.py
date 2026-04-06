import os

from azure.search.documents import SearchClient
from azure.search.documents.models import SearchMode

from models import CardResult

from .client import create_search_client


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
        Search the cards index with the given query.

        Args:
            query: The search query string.
            top:   Maximum number of results to return.

        Returns:
            A list of matching CardResult objects.
        """
        results = self._client.search(
            search_text=query,
            search_mode=SearchMode.ALL,
            top=top,
        )
        return [CardResult.model_validate(dict(result)) for result in results]
