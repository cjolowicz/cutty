"""Unit tests for cutty.templates.domain.renderfiles."""
import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.files import Mode
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles


@pytest.fixture
def path() -> Path:
    """Fixture for a path."""
    filesystem = DictFilesystem({"{x}": "{x}-blob"})
    return Path("{x}", filesystem=filesystem)


def test_renderfiles_default(render: Renderer, path: Path) -> None:
    """It renders the file."""
    binding = Binding("x", "teapot")

    [file] = renderfiles([path], render, [binding])

    assert file.path == PurePath("teapot")
    assert file.mode == Mode.DEFAULT
    assert file.blob == "teapot-blob"


def test_renderfiles_empty_path(render: Renderer, path: Path) -> None:
    """It does not render the file."""
    binding = Binding("x", "")

    assert not list(renderfiles([path], render, [binding]))


def test_renderfiles_invalid_path(render: Renderer, path: Path) -> None:
    """It raises an exception."""
    binding = Binding("x", "..")

    with pytest.raises(Exception):
        next(renderfiles([path], render, [binding]))
