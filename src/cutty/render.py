"""Render templates."""
from typing import Any

from .environment import Environment
from .types import StrMapping


def render_variable(env: Environment, value: Any, context: StrMapping) -> Any:
    """Render the next variable to be displayed in the user prompt."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            render_variable(env, key, context): render_variable(env, val, context)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [render_variable(env, item, context) for item in value]

    template = env.from_string(str(value))

    return template.render(cookiecutter=context)
