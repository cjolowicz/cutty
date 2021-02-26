"""Unit tests for cutty.domain.files."""
import pytest

from cutty.domain.files import RenderableFile
from cutty.domain.files import RenderablePath
from cutty.domain.paths import Path
from cutty.domain.renderables import TrivialRenderable


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
    assert path == Path.fromparts(parts)


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
    renderable = RenderableFile(renderablepath, renderableblob)
    file = renderable.render([])
    assert file.path == Path.fromparts(parts)
    assert file.blob == text
