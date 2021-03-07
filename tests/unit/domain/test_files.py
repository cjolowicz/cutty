"""Unit tests for cutty.domain.files."""
import pytest

from cutty.domain.files import EmptyPathComponent
from cutty.domain.files import InvalidPathComponent
from cutty.domain.files import Mode
from cutty.domain.files import Path
from cutty.domain.files import RenderableFile
from cutty.domain.files import RenderablePath
from cutty.domain.renderables import TrivialRenderable


@pytest.mark.parametrize(
    "parts",
    [
        [""],
        ["example", ""],
        ["", "example"],
        ["example", "", "README.md"],
    ],
)
def test_empty(parts: list[str]) -> None:
    """It raises an exception."""
    with pytest.raises(EmptyPathComponent):
        Path(parts)


@pytest.mark.parametrize(
    "parts",
    [
        ["/", "boot", "vmlinuz"],
        ["\\", "system32", "hal.dll"],
        ["..", "README.md"],
        ["example", ".", "README.md"],
    ],
)
def test_invalid(parts: list[str]) -> None:
    """It raises an exception."""
    with pytest.raises(InvalidPathComponent):
        Path(parts)


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
    ],
)
def test_valid(parts: list[str]) -> None:
    """It returns a Path instance."""
    assert Path(parts)


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
    ],
)
def test_renderable_path(parts: list[str]) -> None:
    """It renders to a Path."""
    renderable = RenderablePath([TrivialRenderable(part) for part in parts])
    path = renderable.render([])
    assert path == Path(parts)


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_renderable_file(parts: list[str], text: str) -> None:
    """It renders to a File."""
    renderablepath = RenderablePath([TrivialRenderable(part) for part in parts])
    renderableblob = TrivialRenderable(text)
    renderable = RenderableFile(renderablepath, Mode.DEFAULT, renderableblob)
    file = renderable.render([])
    assert file.path == Path(parts)
    assert file.mode == Mode.DEFAULT
    assert file.blob == text
