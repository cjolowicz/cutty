"""Unit tests for cutty.adapters.jinja.render."""
import pathlib

import pytest

from cutty.adapters.jinja.render import JinjaRenderer
from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


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
    variable = Binding("value", 42)
    text = jinja_render("{{ value }}", [variable], [])
    assert text == "42"


def test_render_with_context_prefix(cookiecutter_render: Renderer) -> None:
    """It renders a Jinja template with a context prefix."""
    variable = Binding("value", 42)
    text = cookiecutter_render("{{ cookiecutter.value }}", [variable], [])
    assert text == "42"
