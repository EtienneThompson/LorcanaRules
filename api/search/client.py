import os

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


def create_search_client(index_name: str) -> SearchClient:
    """
    Create an Azure AI Search client for the given index.

    Authenticates using DefaultAzureCredential, which works with:
      - Local development: Azure CLI (`az login`), VS Code, environment variables
      - Deployed: managed identity on the Azure Function

    Reads the service endpoint from environment variables:
      AZURE_SEARCH_ENDPOINT  — e.g. https://<service>.search.windows.net
    """
    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=DefaultAzureCredential(),
    )
