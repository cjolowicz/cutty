"""Loading project templates from the filesystem."""
import abc
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.bindings import Binding
from cutty.domain.bindings import Value
from cutty.domain.files import File
from cutty.domain.render import Renderer
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateConfig
from cutty.filesystem.path import Path


class TemplateConfigLoader(abc.ABC):
    """Interface for loading template configurations."""

    @abc.abstractmethod
    def load(self, path: Path) -> TemplateConfig:
        """Load template configuration."""


class RendererFactory(abc.ABC):
    """Interface for creating a renderer."""

    @abc.abstractmethod
    def create(self, path: Path, *, settings: Sequence[Binding[Value]]) -> Renderer:
        """Create a renderer."""


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
        rendererfactory: RendererFactory,
        fileloader: FileLoader,
    ) -> None:
        """Initialize."""
        self.configloader = configloader
        self.rendererfactory = rendererfactory
        self.fileloader = fileloader

    def load(self, path: Path) -> Template:
        """Load a template."""
        config = self.configloader.load(path)
        renderer = self.rendererfactory.create(path, settings=config.settings)
        files = self.fileloader.load(path)
        return Template(config=config, files=files, renderer=renderer)
