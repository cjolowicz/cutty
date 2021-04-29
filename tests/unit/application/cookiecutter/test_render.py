"""Unit tests for cutty.application.cookiecutter.render."""
from collections.abc import Callable
from typing import Any

import pytest

from cutty.application.cookiecutter.render import registerrenderers
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.plugins.adapters.fake import FakeRegistry
from cutty.templates.adapters.hooks import getrendererregistrar
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import Renderer


@pytest.fixture
def rendererfactory() -> Callable[..., Renderer]:
    """Fixture for a renderer factory."""

    def _create(**settings: Any) -> Renderer:
        hooks = FakeRegistry()
        getrenderers = getrendererregistrar(hooks)
        registerrenderers(hooks)
        searchpath = Path(filesystem=DictFilesystem({}))
        config = Config(settings, ())
        renderregistry = getrenderers(searchpath, config)
        return createrenderer(renderregistry)

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

    file1 = File(path1, Mode.DEFAULT, b"{{ do not render }}")
    file2 = File(path2, file1.mode, file1.blob)

    assert render(file1, [Binding("project", "example")]) == file2


def test_binary(render: Renderer) -> None:
    """It does not render binary files."""
    path1 = PurePath("{{ cookiecutter.project }}", "README")
    path2 = PurePath("example", "README")

    file1 = File(path1, Mode.DEFAULT, b"\0{{ binary files are not rendered }}")
    file2 = File(path2, file1.mode, file1.blob)

    assert render(file1, [Binding("project", "example")]) == file2
