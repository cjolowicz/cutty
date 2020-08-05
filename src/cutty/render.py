"""Render templates."""
from typing import Any

from cookiecutter.environment import StrictEnvironment

from .types import StrMapping


def render_variable(env: StrictEnvironment, value: Any, context: StrMapping) -> Any:
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
