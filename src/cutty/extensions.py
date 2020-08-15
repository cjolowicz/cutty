"""Jinja2 extensions."""
import json
import string
from secrets import choice

from jinja2.ext import Extension
from slugify import slugify as pyslugify


def jsonify(obj):
    """Convert a Python object to JSON."""
    return json.dumps(obj, sort_keys=True, indent=4)


def random_ascii_string(length, punctuation=False):
    """Create a random string."""
    corpus = string.ascii_letters
    if punctuation:
        corpus += string.punctuation
    return "".join(choice(corpus) for _ in range(length))


def slugify(value, **kwargs):
    """Slugify a string."""
    return pyslugify(value, **kwargs)


class JsonifyExtension(Extension):
    """Jinja2 extension to convert a Python object to JSON."""

    def __init__(self, environment):
        """Initialize the extension with the given environment."""
        super().__init__(environment)
        environment.filters["jsonify"] = jsonify


class RandomStringExtension(Extension):
    """Jinja2 extension to create a random string."""

    def __init__(self, environment):
        """Jinja2 Extension Constructor."""
        super().__init__(environment)
        environment.globals["random_ascii_string"] = random_ascii_string


class SlugifyExtension(Extension):
    """Jinja2 Extension to slugify string."""

    def __init__(self, environment):
        """Jinja2 Extension constructor."""
        super().__init__(environment)
        environment.filters["slugify"] = slugify
