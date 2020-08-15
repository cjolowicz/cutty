"""Jinja2 extensions."""
import json
import string
from secrets import choice

from jinja2.ext import Extension
from slugify import slugify


def jsonify(obj):
    """Convert a Python object to JSON."""
    return json.dumps(obj, sort_keys=True, indent=4)


def random_ascii_string(length, punctuation=False):
    """Create a random string."""
    corpus = string.ascii_letters
    if punctuation:
        corpus += string.punctuation
    return "".join(choice(corpus) for _ in range(length))


class JsonifyExtension(Extension):
    """Jinja2 extension to convert a Python object to JSON."""

    def __init__(self, environment):
        """Initialize."""
        super().__init__(environment)
        environment.filters["jsonify"] = jsonify


class RandomStringExtension(Extension):
    """Jinja2 extension to create a random string."""

    def __init__(self, environment):
        """Initialize."""
        super().__init__(environment)
        environment.globals["random_ascii_string"] = random_ascii_string


class SlugifyExtension(Extension):
    """Jinja2 extension to slugify a string."""

    def __init__(self, environment):
        """Initialize."""
        super().__init__(environment)
        environment.filters["slugify"] = slugify
