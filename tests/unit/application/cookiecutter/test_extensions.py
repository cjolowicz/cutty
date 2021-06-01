"""Unit tests for cutty.application.cookiecutter.extensions."""
import string
from collections.abc import Callable

import jinja2.ext
import pytest

from cutty.application.cookiecutter.extensions import JsonifyExtension
from cutty.application.cookiecutter.extensions import RandomStringExtension
from cutty.application.cookiecutter.extensions import SlugifyExtension


CreateTemplate = Callable[..., jinja2.Template]


@pytest.fixture
def create_template() -> CreateTemplate:
    """Factory fixture for a Jinja template."""

    def _factory(
        template: str, *, extensions: list[type[jinja2.ext.Extension]]
    ) -> jinja2.Template:
        loader = jinja2.FunctionLoader(lambda _name: template)
        environment = jinja2.Environment(  # noqa: S701
            loader=loader, extensions=extensions
        )
        return environment.get_template("name")

    return _factory


def test_jsonify_extension(create_template: CreateTemplate) -> None:
    """It serializes a value to JSON."""
    template = create_template(
        "{{ value | jsonify }}",
        extensions=[JsonifyExtension],
    )
    assert template.render(value=42) == "42"


@pytest.mark.parametrize("length", [0, 8, 1024])
@pytest.mark.parametrize("punctuation", [False, True])
def test_random_string_extension(
    create_template: CreateTemplate, length: int, punctuation: bool
) -> None:
    """It creates a random string."""
    template = create_template(
        "{{ random_ascii_string(%d, %s) }}" % (length, punctuation),
        extensions=[RandomStringExtension],
    )
    text = template.render()
    assert len(text) == length and all(
        char in string.ascii_letters + string.punctuation for char in text
    )


def test_slugify_extension(create_template: CreateTemplate) -> None:
    """It slugifies the string."""
    template = create_template(
        "{{ value | slugify }}",
        extensions=[SlugifyExtension],
    )
    assert template.render(value="path/to/file") == "path-to-file"
