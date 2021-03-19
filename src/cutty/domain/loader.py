"""Loading project templates from the filesystem."""
import abc
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import RenderableFileLoader
from cutty.domain.filesystem import Path
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.varspecs import RenderableVariableSpecificationLoader
from cutty.domain.varspecs import VariableSpecification


class FileLoader(abc.ABC):
    """Interface for loading project files for a template."""

    @abc.abstractmethod
    def load(self, path: Path) -> Iterator[File]:
        """Load project files."""


class VariableSpecificationLoader(abc.ABC):
    """Interface for loading variable specifications for a template."""

    @abc.abstractmethod
    def load(self, path: Path) -> Iterator[VariableSpecification[Value]]:
        """Load variable specifications."""


class RenderableLoaderFactory(abc.ABC):
    """Interface for creating a renderable loader."""

    @abc.abstractmethod
    def create(self, path: Path) -> RenderableLoader[str]:
        """Create renderable loader."""


class TemplateLoader:
    """A loader for project templates."""

    def __init__(
        self,
        *,
        loaderfactory: RenderableLoaderFactory,
        varloader: VariableSpecificationLoader,
        fileloader: FileLoader,
    ) -> None:
        """Initialize."""
        self.loaderfactory = loaderfactory
        self.varloader = varloader
        self.fileloader = fileloader

    def load(self, path: Path) -> Template:
        """Load a template."""
        loader = self.loaderfactory.create(path)
        variables = map(
            RenderableVariableSpecificationLoader(loader).load,
            self.varloader.load(path),
        )
        files = map(
            RenderableFileLoader(loader).load,
            self.fileloader.load(path),
        )
        return Template(variables=variables, files=files)
