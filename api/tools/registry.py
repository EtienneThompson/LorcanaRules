from tools import SearchCardsTool, SearchRulesTool, Tool

# All tools available to the planner.  Add new tools here as they are implemented.
TOOLS: list[Tool] = [
    SearchCardsTool(),
    SearchRulesTool(),
]
