from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined


class PromptFormatter:
    """
    Renders Jinja2 prompt templates from the prompts directory.

    Templates are organised by component — each component has its own
    sub-folder under ``api/prompts/``.  For example, the planner system
    prompt lives at ``api/prompts/planner/system.j2``.

    Usage::

        formatter = PromptFormatter()
        system_prompt = formatter.render("planner", "system.j2", tools=tools)
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        """
        Args:
            prompts_dir: Path to the root prompts directory.  Defaults to the
                         ``prompts/`` folder that sits alongside this file.
        """
        root = prompts_dir or Path(__file__).parent
        self._env = Environment(
            loader=FileSystemLoader(str(root)),
            # Raise immediately if a variable is undefined rather than silently
            # rendering an empty string — makes template bugs obvious.
            undefined=StrictUndefined,
            # Trim leading whitespace after block tags so the rendered output
            # doesn't end up with extra blank lines from Jinja control blocks.
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, component: str, template_name: str, **kwargs) -> str:
        """
        Render a template and return the result as a string.

        Args:
            component:     Sub-folder name (e.g. ``"planner"``).
            template_name: Template file name including extension
                           (e.g. ``"system.j2"``).
            **kwargs:      Variables passed into the template.

        Returns:
            The rendered prompt string.
        """
        template = self._env.get_template(f"{component}/{template_name}")
        return template.render(**kwargs)
