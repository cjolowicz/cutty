"""Loading project templates from the filesystem."""
import abc
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import RenderableFileLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateConfig
from cutty.domain.variables import Value
from cutty.domain.varspecs import RenderableVariableSpecificationLoader
from cutty.domain.varspecs import VariableSpecification
from cutty.filesystem.path import Path


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
    def create(self, path: Path, config: TemplateConfig) -> RenderableLoader[str]:
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
        config = TemplateConfig(variables=tuple(self.varloader.load(path)))
        loader = self.loaderfactory.create(path, config)
        variables = map(
            RenderableVariableSpecificationLoader(loader).load,
            config.variables,
        )
        files = map(
            RenderableFileLoader(loader).load,
            self.fileloader.load(path),
        )
        return Template(variables=variables, files=files)
