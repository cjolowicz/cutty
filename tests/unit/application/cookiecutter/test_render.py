"""Unit tests for cutty.application.cookiecutter.render."""
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
def render() -> Renderer:
    """Fixture for a renderer."""
    searchpath = Path(filesystem=DictFilesystem({}))
    config = Config({}, ())
    return loadrenderer(searchpath, config)


def test_render_list_empty(render: Renderer) -> None:
    """It renders an empty list as itself."""
    assert render([], []) == []


def test_render_dict_empty(render: Renderer) -> None:
    """It renders an empty dict as itself."""
    assert render({}, []) == {}


def test_copy_without_render() -> None:
    """It does not render files matching 'copy_without_render' patterns."""
    searchpath = Path(filesystem=DictFilesystem({}))
    config = Config({"_copy_without_render": ["*.norender"]}, ())
    render = loadrenderer(searchpath, config)

    path = PurePath("{{ cookiecutter.project }}", "README.norender")
    path2 = PurePath("example", "README.norender")

    file = File(path, Mode.DEFAULT, "{{ do not render }}")
    file2 = File(path2, file.mode, file.blob)

    assert render(file, [Binding("project", "example")]) == file2
