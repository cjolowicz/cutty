"""Unit tests for cutty.domain.templates."""
from collections.abc import Iterable
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import FileRepository
from cutty.domain.files import RenderableFileLoader
from cutty.domain.files import RenderableFileRepository
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.varspecs import DefaultVariableBuilder


class FakeFileRepository(FileRepository):
    """A fake repository of files."""

    def __init__(self, files: Iterable[File] = ()) -> None:
        """Initialize."""
        self.files = files

    def load(self) -> Iterator[File]:
        """Iterate over the files in the repository."""
        return iter(self.files)


def test_template(
    renderable_loader: RenderableLoader[str],
) -> None:
    """It can be rendered."""
    loader = RenderableFileLoader(renderable_loader)
    repository = RenderableFileRepository(FakeFileRepository(), loader)
    template = Template(files=repository, variables=[])
    template.render(DefaultVariableBuilder())
