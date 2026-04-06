import re

from .models import ToolCall

# Matches an entire tool-call line, e.g.:
#   search_cards(query=Elsa)
#   search_rules(query="what is questing", top=3)
_CALL_RE = re.compile(r"^(\w+)\((.*)\)$", re.DOTALL)

# Matches a single key=value argument where the value is either:
#   - a double-quoted string:  key="some value with spaces"
#   - an unquoted token:       key=SomeValue  (no spaces or commas)
_ARG_RE = re.compile(r'(\w+)=(?:"([^"]*)"|((?:[^,\s\)]+)))')


def parse_tool_call(line: str) -> ToolCall | None:
    """
    Parse a single line into a :class:`ToolCall`.

    Accepts the function-call-style format produced by the planner LLM::

        tool_name(param1=value1, param2="multi word value")

    Returns ``None`` if the line does not match the expected format, so
    callers can safely skip blank lines or any stray prose the model emits.

    Args:
        line: A single stripped line of text from the planner's output.

    Returns:
        A :class:`ToolCall` if the line is a valid tool call, else ``None``.
    """
    line = line.strip()
    call_match = _CALL_RE.match(line)
    if not call_match:
        return None

    name = call_match.group(1)
    args_str = call_match.group(2).strip()

    arguments: dict[str, str] = {}
    for arg_match in _ARG_RE.finditer(args_str):
        key = arg_match.group(1)
        # Group 2 → quoted value, group 3 → unquoted value
        value = arg_match.group(2) if arg_match.group(2) is not None else arg_match.group(3)
        arguments[key] = value

    return ToolCall(name=name, arguments=arguments)
