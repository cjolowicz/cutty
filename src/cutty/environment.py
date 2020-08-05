"""Jinja2 environment and extensions loading."""
from typing import Any
from typing import Optional

import jinja2
from cookiecutter.exceptions import UnknownExtension

from .types import StrMapping


DEFAULT_EXTENSIONS = [
    "cookiecutter.extensions.JsonifyExtension",
    "cookiecutter.extensions.RandomStringExtension",
    "cookiecutter.extensions.SlugifyExtension",
    "jinja2_time.TimeExtension",
]


class Environment(jinja2.Environment):
    """Jinja2 environment."""

    def __init__(self, context: Optional[StrMapping] = None, **kwargs: Any) -> None:
        """Initialize."""
        if context is None:
            context = {}

        extensions = context.get("cookiecutter", {}).get("_extensions", [])
        extensions = [str(extension) for extension in extensions]
        extensions = DEFAULT_EXTENSIONS + extensions

        try:
            super().__init__(
                undefined=jinja2.StrictUndefined, extensions=extensions, **kwargs
            )
        except ImportError as error:
            raise UnknownExtension(f"Unable to load extension: {error}")
