"""Unit tests for cutty.domain.files."""
import pytest

from cutty.domain.files import EmptyPathComponent
from cutty.domain.files import File
from cutty.domain.files import InvalidPathComponent
from cutty.domain.files import Mode
from cutty.domain.files import Path
from cutty.domain.files import RenderableFile
from cutty.domain.files import RenderableFileLoader
from cutty.domain.files import RenderableFileRenderer
from cutty.domain.files import RenderableFileRepository
from cutty.domain.files import RenderablePath
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
    file = File(Path(parts), Mode.DEFAULT, text)
    renderable = loader.load(file)
    assert file == renderable.render([])


@pytest.mark.parametrize(
    "parts,text",
    [
        (["README.md"], "# example\n"),
        (["example", "README.md"], "# example\n"),
    ],
)
def test_renderable_file_repository(
    parts: list[str],
    text: str,
    renderable_loader: RenderableLoader[str],
) -> None:
    """It loads renderable files."""
    file = File(Path(parts), Mode.DEFAULT, text)
    [renderable] = RenderableFileRepository(
        [file],
        RenderableFileLoader(renderable_loader),
    )
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
    file = File(Path(parts), Mode.DEFAULT, text)
    repository = RenderableFileRepository(
        [file],
        RenderableFileLoader(renderable_loader),
    )
    renderer = RenderableFileRenderer(repository)
    [rendered] = renderer.render([])
    assert file == rendered


def test_renderable_file_renderer_empty_path(
    renderable_loader: RenderableLoader[str],
) -> None:
    """It skips files with an empty path segment."""
    variable = Variable("project", "")
    file = File(Path(["{project}", "README.md"]), Mode.DEFAULT, "text")
    repository = RenderableFileRepository(
        [file],
        RenderableFileLoader(renderable_loader),
    )
    renderer = RenderableFileRenderer(repository)
    rendered = renderer.render([variable])
    assert not list(rendered)
