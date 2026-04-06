from .base import Tool


class ToolRegistry:
    """
    Central registry mapping tool names to tool instances.

    Usage::

        registry = ToolRegistry()
        registry.register(SearchCardsTool(), SearchRulesTool())

        # For the planner prompt:
        tools = registry.all()

        # For the executor:
        tool = registry.get("search_cards")
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, *tools: Tool) -> None:
        """Add one or more tools to the registry."""
        for tool in tools:
            self._tools[tool.name] = tool

    def all(self) -> list[Tool]:
        """Return all registered tool instances."""
        return list(self._tools.values())

    def get(self, name: str) -> Tool:
        """
        Return the tool registered under *name*.

        Raises:
            KeyError: if no tool with that name has been registered.
        """
        try:
            return self._tools[name]
        except KeyError:
            raise KeyError(f"No tool registered with name {name!r}") from None


registry = ToolRegistry()
