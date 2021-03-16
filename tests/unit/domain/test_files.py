"""Unit tests for cutty.domain.files."""
import pytest

from cutty.domain.files import Buffer
from cutty.domain.files import EmptyPathComponent
from cutty.domain.files import InvalidPathComponent
from cutty.domain.files import loadfiles
from cutty.domain.files import Mode
from cutty.domain.files import RenderableBuffer
from cutty.domain.files import RenderableFileLoader
from cutty.domain.files import RenderablePath
from cutty.domain.files import renderfiles
from cutty.domain.filesystem import PurePath
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.variables import Variable


@pytest.mark.parametrize(
    "parts",
    [
        [""],
        ["example", ""],
        ["", "example"],
        ["example", "", "README.md"],
    ],
)
def test_renderable_path_empty(parts: list[str]) -> None:
    """It raises an exception."""
    renderable = RenderablePath([TrivialRenderable(part) for part in parts])
    with pytest.raises(EmptyPathComponent):
        renderable.render([])


@pytest.mark.parametrize(
    "parts",
    [
        ["/", "boot", "vmlinuz"],
        ["\\", "system32", "hal.dll"],
        ["..", "README.md"],
        ["example", ".", "README.md"],
    ],
)
def test_renderable_path_invalid(parts: list[str]) -> None:
    """It raises an exception."""
    renderable = RenderablePath([TrivialRenderable(part) for part in parts])
    with pytest.raises(InvalidPathComponent):
        renderable.render([])


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
    ],
)
def test_renderable_path_good(parts: list[str]) -> None:
    """It renders to a PurePath."""
    renderable = RenderablePath([TrivialRenderable(part) for part in parts])
    path = renderable.render([])
    assert path == PurePath(*parts)


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_renderable_buffer(parts: list[str], text: str) -> None:
    """It renders to a Buffer."""
    renderablepath = RenderablePath([TrivialRenderable(part) for part in parts])
    renderableblob = TrivialRenderable(text)
    renderable = RenderableBuffer(renderablepath, Mode.DEFAULT, renderableblob)
    file = renderable.render([])
    assert file.path == PurePath(*parts)
    assert file.mode == Mode.DEFAULT
    assert file.read() == text


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_renderable_file_loader(
    parts: list[str], text: str, renderable_loader: RenderableLoader[str]
) -> None:
    """It loads renderable files."""
    loader = RenderableFileLoader(renderable_loader)
    file = Buffer(PurePath(*parts), Mode.DEFAULT, text)
    renderable = loader.load(file)
    assert file == renderable.render([])


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_loadfiles(
    parts: list[str],
    text: str,
    renderable_loader: RenderableLoader[str],
) -> None:
    """It loads renderable files."""
    file = Buffer(PurePath(*parts), Mode.DEFAULT, text)
    loader = RenderableFileLoader(renderable_loader)
    [renderable] = loadfiles([file], loader)
    assert file == renderable.render([])


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_renderable_file_renderer(
    parts: list[str],
    text: str,
    renderable_loader: RenderableLoader[str],
) -> None:
    """It renders files."""
    file = Buffer(PurePath(*parts), Mode.DEFAULT, text)
    loader = RenderableFileLoader(renderable_loader)
    repository = loadfiles([file], loader)
    [rendered] = renderfiles(repository, [])
    assert file == rendered


def test_renderable_file_renderer_empty_path(
    renderable_loader: RenderableLoader[str],
) -> None:
    """It skips files with an empty path segment."""
    variable = Variable("project", "")
    file = Buffer(PurePath("{project}", "README.md"), Mode.DEFAULT, "text")
    loader = RenderableFileLoader(renderable_loader)
    repository = loadfiles([file], loader)
    rendered = renderfiles(repository, [variable])
    assert not list(rendered)
