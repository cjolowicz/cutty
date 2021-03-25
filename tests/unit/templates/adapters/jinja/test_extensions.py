"""Unit tests for cutty.templates.adapters.jinja.extensions."""
import string
from collections.abc import Callable

import jinja2.ext
import pytest

from cutty.templates.adapters.jinja import extensions


@pytest.mark.parametrize(
    "import_path",
    [
        "json",
        "os.path",
        "xml.sax",
        "xml.sax.saxutils:escape",
        "xml.sax.saxutils.escape",
    ],
)
def test_import_object(import_path: str) -> None:
    """It imports the object."""
    assert extensions.import_object(import_path)


def test_load_default() -> None:
    """It returns something."""
    assert extensions.load()


def test_load_extra() -> None:
    """It returns something."""
    assert extensions.load(extra=["jinja2_time.TimeExtension"])


def test_load_type_error() -> None:
    """It raises an error."""
    with pytest.raises(extensions.TemplateExtensionTypeError):
        extensions.load(extra=["os.path"])


CreateTemplate = Callable[..., jinja2.Template]


@pytest.fixture
def create_template() -> CreateTemplate:
    """Factory fixture for a Jinja template."""

    def _factory(
        template: str, *, extensions: list[jinja2.ext.Extension]
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
        extensions=[extensions.JsonifyExtension],
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
        extensions=[extensions.RandomStringExtension],
    )
    text = template.render()
    assert len(text) == length and all(
        char in string.ascii_letters + string.punctuation for char in text
    )


def test_slugify_extension(create_template: CreateTemplate) -> None:
    """It slugifies the string."""
    template = create_template(
        "{{ value | slugify }}",
        extensions=[extensions.SlugifyExtension],
    )
    assert template.render(value="path/to/file") == "path-to-file"
