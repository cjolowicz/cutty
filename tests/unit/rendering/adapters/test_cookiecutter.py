"""Unit tests for cutty.rendering.adapters.cookiecutter."""
from collections.abc import Callable
from typing import Any

import pytest

from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.rendering.adapters.cookiecutter import CookiecutterConfig
from cutty.rendering.adapters.cookiecutter import createcookiecutterrenderer
from cutty.rendering.domain.render import Renderer
from cutty.variables.domain.bindings import Binding


@pytest.fixture
def rendererfactory() -> Callable[..., Renderer]:
    """Fixture for a renderer factory."""

    def _create(**settings: Any) -> Renderer:
        searchpath = Path(filesystem=DictFilesystem({}))
        config = CookiecutterConfig(settings, ())
        return createcookiecutterrenderer(searchpath, config)

    return _create


@pytest.fixture
def render(rendererfactory: Callable[..., Renderer]) -> Renderer:
    """Fixture for a renderer."""
    return rendererfactory()


def test_render_list_empty(render: Renderer) -> None:
    """It renders an empty list as itself."""
    assert render([], []) == []


def test_render_dict_empty(render: Renderer) -> None:
    """It renders an empty dict as itself."""
    assert render({}, []) == {}


def test_copy_without_render(rendererfactory: Callable[..., Renderer]) -> None:
    """It does not render files matching 'copy_without_render' patterns."""
    render = rendererfactory(_copy_without_render=["*.norender"])

    path1 = PurePath("{{ cookiecutter.project }}", "README.norender")
    path2 = PurePath("example", "README.norender")

    file1 = RegularFile(path1, b"{{ do not render }}")
    file2 = RegularFile(path2, file1.blob)

    assert render(file1, [Binding("project", "example")]) == file2


def test_binary(render: Renderer) -> None:
    """It does not render binary files."""
    path1 = PurePath("{{ cookiecutter.project }}", "README")
    path2 = PurePath("example", "README")

    file1 = RegularFile(path1, b"\0{{ binary files are not rendered }}")
    file2 = RegularFile(path2, file1.blob)

    assert render(file1, [Binding("project", "example")]) == file2
