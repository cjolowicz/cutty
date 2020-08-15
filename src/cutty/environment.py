"""Jinja2 environment and extensions loading."""
from typing import Any

import jinja2

from . import exceptions
from .types import Context


DEFAULT_EXTENSIONS = [
    "cutty.extensions.JsonifyExtension",
    "cutty.extensions.RandomStringExtension",
    "cutty.extensions.SlugifyExtension",
    "jinja2_time.TimeExtension",
]


class Environment(jinja2.Environment):
    """Jinja2 environment."""

    def __init__(self, context: Context, **kwargs: Any) -> None:
        """Initialize."""
        extensions = context.get("cookiecutter", {}).get("_extensions", [])
        extensions = [str(extension) for extension in extensions]
        extensions = DEFAULT_EXTENSIONS + extensions

        try:
            super().__init__(
                undefined=jinja2.StrictUndefined, extensions=extensions, **kwargs
            )
        except ImportError as error:
            raise exceptions.UnknownExtension(f"Unable to load extension: {error}")
