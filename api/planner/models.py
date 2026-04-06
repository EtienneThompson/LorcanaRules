from dataclasses import dataclass, field


@dataclass
class ToolCall:
    """
    Represents a single tool call emitted by the planner.

    Attributes:
        name:      The tool's snake_case name (e.g. ``"search_cards"``).
        arguments: Mapping of parameter name → value, both as strings.
                   Type coercion to the tool's expected types is the
                   responsibility of the tool's ``execute()`` method.
    """

    name: str
    arguments: dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:
        args = ", ".join(f"{k}={v!r}" for k, v in self.arguments.items())
        return f"{self.name}({args})"
