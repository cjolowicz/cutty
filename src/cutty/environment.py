"""Jinja2 environment and extensions loading."""
from typing import Any

import jinja2

from . import exceptions
from .types import StrMapping


DEFAULT_EXTENSIONS = [
    "cookiecutter.extensions.JsonifyExtension",
    "cookiecutter.extensions.RandomStringExtension",
    "cookiecutter.extensions.SlugifyExtension",
    "jinja2_time.TimeExtension",
]


class Environment(jinja2.Environment):
    """Jinja2 environment."""

    def __init__(self, context: StrMapping, **kwargs: Any) -> None:
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
