"""Jinja2 extensions."""
import json
import string
from secrets import choice
from typing import Any

import jinja2.ext
from slugify import slugify


def jsonify(obj: Any) -> str:
    """Convert a Python object to JSON."""
    return json.dumps(obj, sort_keys=True, indent=4)


def random_ascii_string(length: int, punctuation: bool = False) -> str:
    """Create a random string."""
    corpus = string.ascii_letters
    if punctuation:
        corpus += string.punctuation
    return "".join(choice(corpus) for _ in range(length))


class JsonifyExtension(jinja2.ext.Extension):
    """Jinja2 extension to convert a Python object to JSON."""

    def __init__(self, environment: jinja2.Environment) -> None:
        """Initialize."""
        super().__init__(environment)
        environment.filters["jsonify"] = jsonify


class RandomStringExtension(jinja2.ext.Extension):
    """Jinja2 extension to create a random string."""

    def __init__(self, environment: jinja2.Environment) -> None:
        """Initialize."""
        super().__init__(environment)
        environment.globals["random_ascii_string"] = random_ascii_string


class SlugifyExtension(jinja2.ext.Extension):
    """Jinja2 extension to slugify a string."""

    def __init__(self, environment: jinja2.Environment) -> None:
        """Initialize."""
        super().__init__(environment)
        environment.filters["slugify"] = slugify
