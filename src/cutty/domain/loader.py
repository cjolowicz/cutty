"""Loading project templates from the filesystem."""
import abc
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.files import File
from cutty.domain.files import RenderableFileLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateConfig
from cutty.domain.variables import Value
from cutty.domain.variables import Variable
from cutty.domain.varspecs import RenderableVariableSpecificationLoader
from cutty.filesystem.path import Path


class TemplateConfigLoader(abc.ABC):
    """Interface for loading template configurations."""

    @abc.abstractmethod
    def load(self, path: Path) -> TemplateConfig:
        """Load template configuration."""


class RenderableLoaderFactory(abc.ABC):
    """Interface for creating a renderable loader."""

    @abc.abstractmethod
    def create(
        self, path: Path, *, settings: Sequence[Variable[Value]]
    ) -> RenderableLoader[str]:
        """Create renderable loader."""


class FileLoader(abc.ABC):
    """Interface for loading project files for a template."""

    @abc.abstractmethod
    def load(self, path: Path) -> Iterator[File]:
        """Load project files."""


class TemplateLoader:
    """A loader for project templates."""

    def __init__(
        self,
        *,
        configloader: TemplateConfigLoader,
        loaderfactory: RenderableLoaderFactory,
        fileloader: FileLoader,
    ) -> None:
        """Initialize."""
        self.configloader = configloader
        self.loaderfactory = loaderfactory
        self.fileloader = fileloader

    def load(self, path: Path) -> Template:
        """Load a template."""
        config = self.configloader.load(path)
        loader = self.loaderfactory.create(path, settings=config.settings)
        variables = map(
            RenderableVariableSpecificationLoader(loader).load,
            config.variables,
        )
        files = map(
            RenderableFileLoader(loader).load,
            self.fileloader.load(path),
        )
        return Template(variables=variables, files=files)
