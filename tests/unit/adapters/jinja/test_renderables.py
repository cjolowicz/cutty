"""Unit tests for cutty.adapters.jinja.renderables."""
import pathlib
from typing import Callable

import pytest

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.domain.paths import Path
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Variable


SaveTemplate = Callable[[Path, str], None]


@pytest.fixture
def save_template(tmp_path: pathlib.Path) -> SaveTemplate:
    """Factory fixture to write a template to disk."""

    def _factory(path: Path, text: str) -> None:
        template = tmp_path.joinpath(*path.parts)
        template.parent.mkdir(exist_ok=True, parents=True)
        template.write_text(text)

    return _factory


@pytest.fixture
def loader(tmp_path: pathlib.Path) -> RenderableLoader:
    """Fixture for a Jinja loader."""
    return JinjaRenderableLoader.create(tmp_path)


@pytest.fixture
def cookiecutter_loader(tmp_path: pathlib.Path) -> RenderableLoader:
    """Fixture for a Jinja loader with a cookiecutter prefix."""
    return JinjaRenderableLoader.create(tmp_path, context_prefix="cookiecutter")


def test_load(loader: RenderableLoader) -> None:
    """It loads a Jinja template."""
    variable = Variable("value", 42)
    renderable = loader.load("{{ value }}")
    text = renderable.render([variable])
    assert text == "42"


def test_load_with_context_prefix(cookiecutter_loader: RenderableLoader) -> None:
    """It loads a Jinja template with a context prefix."""
    variable = Variable("value", 42)
    renderable = cookiecutter_loader.load("{{ cookiecutter.value }}")
    text = renderable.render([variable])
    assert text == "42"


def test_get(loader: RenderableLoader, save_template: SaveTemplate) -> None:
    """It loads a Jinja template."""
    variable = Variable("value", 42)
    path = Path(("template", "module"))
    save_template(path, "{{ value }}")

    renderable = loader.get(path)
    text = renderable.render([variable])

    assert text == "42"
