"""Unit tests for cutty.application.cookiecutter.render."""
from collections.abc import Callable
from typing import Any

import pytest

from cutty.application.cookiecutter.render import loadrenderer
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode
from cutty.templates.domain.render import Renderer


@pytest.fixture
def createrenderer() -> Callable[..., Renderer]:
    """Fixture for a renderer factory."""

    def _create(**settings: Any) -> Renderer:
        searchpath = Path(filesystem=DictFilesystem({}))
        config = Config(settings, ())
        return loadrenderer(searchpath, config)

    return _create


@pytest.fixture
def render(createrenderer: Callable[..., Renderer]) -> Renderer:
    """Fixture for a renderer."""
    return createrenderer()


def test_render_list_empty(render: Renderer) -> None:
    """It renders an empty list as itself."""
    assert render([], []) == []


def test_render_dict_empty(render: Renderer) -> None:
    """It renders an empty dict as itself."""
    assert render({}, []) == {}


def test_copy_without_render(createrenderer: Callable[..., Renderer]) -> None:
    """It does not render files matching 'copy_without_render' patterns."""
    render = createrenderer(_copy_without_render=["*.norender"])

    path1 = PurePath("{{ cookiecutter.project }}", "README.norender")
    path2 = PurePath("example", "README.norender")

    file1 = File(path1, Mode.DEFAULT, b"{{ do not render }}")
    file2 = File(path2, file1.mode, file1.blob)

    assert render(file1, [Binding("project", "example")]) == file2
