"""Unit tests for cutty.adapters.jinja.renderables."""
import pathlib

import pytest

from cutty.adapters.filesystem.filesystem import DiskFilesystem
from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Variable


@pytest.fixture
def loader(tmp_path: pathlib.Path) -> JinjaRenderableLoader:
    """Fixture for a Jinja loader."""
    filesystem = DiskFilesystem(tmp_path)
    return JinjaRenderableLoader.create(searchpath=[filesystem.root])


@pytest.fixture
def cookiecutter_loader(tmp_path: pathlib.Path) -> RenderableLoader[str]:
    """Fixture for a Jinja loader with a cookiecutter prefix."""
    filesystem = DiskFilesystem(tmp_path)
    return JinjaRenderableLoader.create(
        searchpath=[filesystem.root], context_prefix="cookiecutter"
    )


def test_load(loader: RenderableLoader[str]) -> None:
    """It loads a Jinja template."""
    variable = Variable("value", 42)
    renderable = loader.load("{{ value }}")
    text = renderable.render([variable])
    assert text == "42"


def test_load_with_context_prefix(cookiecutter_loader: RenderableLoader[str]) -> None:
    """It loads a Jinja template with a context prefix."""
    variable = Variable("value", 42)
    renderable = cookiecutter_loader.load("{{ cookiecutter.value }}")
    text = renderable.render([variable])
    assert text == "42"
