"""Unit tests for cutty.templates.adapters.jinja.render."""
import pathlib

import pytest

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.jinja.render import import_object
from cutty.templates.adapters.jinja.render import JinjaRenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer


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
    assert import_object(import_path)


@pytest.fixture
def jinja_render(render: Renderer, tmp_path: pathlib.Path) -> Renderer:
    """Fixture for a Jinja renderer."""
    root = Path(filesystem=DiskFilesystem(tmp_path))
    render.register(str, JinjaRenderer.create(searchpath=[root]))
    return render


@pytest.fixture
def cookiecutter_render(render: Renderer, tmp_path: pathlib.Path) -> Renderer:
    """Fixture for a Jinja renderer with a cookiecutter prefix."""
    root = Path(filesystem=DiskFilesystem(tmp_path))
    render.register(
        str, JinjaRenderer.create(searchpath=[root], context_prefix="cookiecutter")
    )
    return render


def test_render(jinja_render: Renderer) -> None:
    """It renders a Jinja template."""
    variable = Binding("value", "teapot")
    text = jinja_render("{{ value }}", [variable])
    assert text == "teapot"


def test_render_with_context_prefix(cookiecutter_render: Renderer) -> None:
    """It renders a Jinja template with a context prefix."""
    variable = Binding("value", "teapot")
    text = cookiecutter_render("{{ cookiecutter.value }}", [variable])
    assert text == "teapot"
