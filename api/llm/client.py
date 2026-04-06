import os
from collections.abc import Generator

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI


def _create_client() -> tuple[AzureOpenAI, str]:
    """
    Create an AzureOpenAI client and return it alongside the deployment name.

    Authenticates using DefaultAzureCredential (Azure CLI locally,
    managed identity when deployed).

    Required environment variables:
      AZURE_OPENAI_ENDPOINT    — e.g. https://<resource>.openai.azure.com/
      AZURE_OPENAI_DEPLOYMENT  — the deployed model name, e.g. gpt-4o
    """
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-12-01-preview",
    )
    return client, deployment


class AzureOpenAIClient:
    """Wrapper around Azure OpenAI supporting full and streaming responses."""

    def __init__(self) -> None:
        self._client, self._deployment = _create_client()

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """
        Send a chat completion request and return the full response text.

        Args:
            messages:    List of {"role": ..., "content": ...} dicts.
            temperature: Sampling temperature.
            max_tokens:  Maximum tokens in the response.

        Returns:
            The assistant's reply as a string.
        """
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return response.choices[0].message.content

    def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """
        Send a chat completion request and yield response text chunks as they arrive.

        Args:
            messages:    List of {"role": ..., "content": ...} dicts.
            temperature: Sampling temperature.
            max_tokens:  Maximum tokens in the response.

        Yields:
            Text delta strings from the model.
        """
        response = self._client.chat.completions.create(
            model=self._deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
