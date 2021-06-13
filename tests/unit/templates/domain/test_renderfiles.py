"""Unit tests for cutty.templates.domain.renderfiles."""
import pytest

from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles


@pytest.fixture
def path() -> Path:
    """Fixture for a path."""
    filesystem = DictFilesystem({"dir": {"{x}": "{x}-blob"}})
    return Path("dir", filesystem=filesystem)


def test_renderfiles_default(render: Renderer, path: Path) -> None:
    """It renders the file."""
    binding = Binding("x", "teapot")

    [file] = renderfiles([path], render, [binding])

    assert isinstance(file, RegularFile)
    assert file.path.parts == ("dir", "teapot")
    assert file.blob == b"teapot-blob"


def test_renderfiles_empty_path(render: Renderer, path: Path) -> None:
    """It does not render the file."""
    binding = Binding("x", "")

    assert not list(renderfiles([path], render, [binding]))


def test_renderfiles_invalid_path(render: Renderer, path: Path) -> None:
    """It raises an exception."""
    binding = Binding("x", "..")

    with pytest.raises(Exception):
        next(renderfiles([path], render, [binding]))
