"""Unit tests for cutty.templates.adapters.jinja."""
import pathlib

import jinja2
import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.jinja import createjinjarenderer
from cutty.templates.adapters.jinja import import_object
from cutty.templates.adapters.jinja import load_extension
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import asrendercontinuation
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
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


@pytest.mark.parametrize(
    "import_path",
    [
        "jinja2_time.TimeExtension",
    ],
)
def test_load_extension_valid(import_path: str) -> None:
    """It loads the extension."""
    extension = load_extension(import_path)
    assert issubclass(extension, jinja2.ext.Extension)


@pytest.mark.parametrize(
    "import_path",
    [
        "json",
    ],
)
def test_load_extension_invalid(import_path: str) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        load_extension(import_path)


def test_loader_valid() -> None:
    """It loads from the filesystem."""
    binding = Binding("x", "teapot")
    root = Path(filesystem=DictFilesystem({"template": "{{ x }}"}))
    render_ = createjinjarenderer(searchpath=[root])
    # Render it twice to trigger Jinja2's caching logic.
    for _ in range(2):
        text = render_("{% include 'template' %}", [binding])
    assert text == "teapot"


def test_loader_invalid() -> None:
    """It raises an exception."""
    binding = Binding("x", "teapot")
    root = Path(filesystem=DictFilesystem({"template": "{{ x }}", "dir": {}}))
    render_ = createjinjarenderer(searchpath=[root])
    with pytest.raises(Exception):
        render_("{% include 'dir/../template' %}", [binding])


def test_loader_not_found() -> None:
    """It raises an exception."""
    binding = Binding("x", "teapot")
    root = Path(filesystem=DictFilesystem({}))
    render_ = createjinjarenderer(searchpath=[root])
    with pytest.raises(Exception):
        render_("{% include 'template' %}", [binding])


@pytest.fixture
def jinja_render(tmp_path: pathlib.Path) -> Renderer:
    """Fixture for a Jinja renderer."""
    root = Path(filesystem=DiskFilesystem(tmp_path))
    rendertext = createjinjarenderer(searchpath=[root])
    return createrenderer(
        {**defaultrenderregistry, str: asrendercontinuation(rendertext)}
    )


@pytest.fixture
def cookiecutter_render(tmp_path: pathlib.Path) -> Renderer:
    """Fixture for a Jinja renderer with a cookiecutter prefix."""
    root = Path(filesystem=DiskFilesystem(tmp_path))
    rendertext = createjinjarenderer(searchpath=[root], context_prefix="cookiecutter")
    return createrenderer(
        {**defaultrenderregistry, str: asrendercontinuation(rendertext)}
    )


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


def test_render_with_extra_context(tmp_path: pathlib.Path) -> None:
    """It renders a Jinja template with extra context."""
    root = Path(filesystem=DiskFilesystem(tmp_path))
    rendertext = createjinjarenderer(
        searchpath=[root], extra_context={"value": "teapot"}
    )
    render = createrenderer(
        {**defaultrenderregistry, str: asrendercontinuation(rendertext)}
    )
    text = render("{{ value }}", [])
    assert text == "teapot"
