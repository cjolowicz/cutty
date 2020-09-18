"""Jinja2 extensions."""
import json
import string
from secrets import choice
from typing import Any
from typing import cast
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type

import jinja2.ext
import jinja2_time
from slugify import slugify

from . import exceptions
from .utils import import_object


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


DEFAULT_EXTENSIONS = [
    JsonifyExtension,
    RandomStringExtension,
    SlugifyExtension,
    jinja2_time.TimeExtension,
]


def load_extension(import_path: str) -> Type[jinja2.ext.Extension]:
    """Import a Jinja extension from the specified path."""
    with exceptions.TemplateExtensionNotFound(import_path):
        extension = import_object(import_path)

    if not issubclass(extension, jinja2.ext.Extension):
        raise exceptions.TemplateExtensionTypeError(import_path, type(extension))

    return cast(Type[jinja2.ext.Extension], extension)


def load(*, extra: Optional[Iterable[str]] = None) -> List[Type[jinja2.ext.Extension]]:
    """Return the default Jinja extensions, plus any additional ones specified."""
    extensions = DEFAULT_EXTENSIONS[:]

    if extra is not None:
        extensions.extend(load_extension(path) for path in extra)

    return extensions
