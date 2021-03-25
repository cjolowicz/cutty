"""Jinja extensions."""
import json
import string
from collections.abc import Iterable
from dataclasses import dataclass
from secrets import choice
from typing import Any

import jinja2.ext
import jinja2_time
from slugify import slugify

from cutty.util.reraise import reraise


@dataclass
class TemplateExtensionNotFound(Exception):
    """The template extension was not found."""

    extension: str


@dataclass
class TemplateExtensionTypeError(Exception):
    """The template extension does not have the expected type."""

    extension: str
    type: str


def import_object(import_path: str) -> Any:
    """Import the object at the given import path.

    Import paths consist of the dotted module name, optionally followed by a
    colon or dot, and the module attribute at which the object is located.

    For example:

    - ``json``
    - ``os.path``
    - ``xml.sax.saxutils:escape``
    - ``xml.sax.saxutils.escape``

    This function mirrors the implementation of ``jinja2.utils.import_string``.
    """
    if ":" in import_path:
        module_name, _, attribute = import_path.rpartition(":")
    elif "." in import_path:
        module_name, _, attribute = import_path.rpartition(".")
    else:
        return __import__(import_path)

    module = __import__(module_name, None, None, [attribute])
    return getattr(module, attribute)


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
    """Jinja extension to convert a Python object to JSON."""

    def __init__(self, environment: jinja2.Environment) -> None:
        """Initialize."""
        super().__init__(environment)
        environment.filters["jsonify"] = jsonify


class RandomStringExtension(jinja2.ext.Extension):
    """Jinja extension to create a random string."""

    def __init__(self, environment: jinja2.Environment) -> None:
        """Initialize."""
        super().__init__(environment)
        environment.globals["random_ascii_string"] = random_ascii_string


class SlugifyExtension(jinja2.ext.Extension):
    """Jinja extension to slugify a string."""

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


def load_extension(import_path: str) -> type[jinja2.ext.Extension]:
    """Import a Jinja extension from the specified path."""
    with reraise(TemplateExtensionNotFound(import_path)):
        extension = import_object(import_path)

    if not (
        isinstance(extension, type) and issubclass(extension, jinja2.ext.Extension)
    ):
        raise TemplateExtensionTypeError(import_path, str(type(extension)))

    return extension


def load(*, extra: Iterable[str] = ()) -> list[type[jinja2.ext.Extension]]:
    """Return the default Jinja extensions, plus any additional ones specified."""
    extensions = DEFAULT_EXTENSIONS[:]
    extensions.extend(load_extension(path) for path in extra)

    return extensions
