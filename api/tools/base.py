from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """
    Abstract base class for all pipeline tools.

    Subclasses define a name, natural-language description, and a JSON Schema
    for their parameters.  The `definition()` method returns the OpenAI
    function-calling dict that the planner LLM receives, and `execute()` runs
    the actual work.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique snake_case identifier used by the planner when calling this tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human/LLM-readable description of what this tool does."""

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        JSON Schema object describing the tool's arguments.
        Returned verbatim inside the OpenAI function definition.
        """

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Run the tool with the provided arguments and return its result."""

    # ---------------------------------------------------------------------- #
    # Helpers                                                                  #
    # ---------------------------------------------------------------------- #

    def definition(self) -> dict:
        """
        Return the OpenAI function-calling definition for this tool.

        Compatible with the ``tools`` parameter accepted by
        ``AzureOpenAI.chat.completions.create()``.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
