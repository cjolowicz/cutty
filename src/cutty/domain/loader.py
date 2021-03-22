"""Loading project templates from the filesystem."""
import abc
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable
from cutty.filesystem.path import Path


@dataclass
class TemplateConfig:
    """Template configuration."""

    settings: tuple[Binding, ...]
    variables: tuple[Variable, ...]


TemplateConfigLoader = Callable[[Path], TemplateConfig]


class RendererFactory(abc.ABC):
    """Interface for creating a renderer."""

    @abc.abstractmethod
    def create(self, path: Path, *, settings: Sequence[Binding]) -> Renderer:
        """Create a renderer."""
