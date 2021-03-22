"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator

from cutty.domain.binders import RenderBinder
from cutty.domain.files import FileStorage
from cutty.domain.loader import RendererLoader
from cutty.domain.loader import TemplateConfigLoader
from cutty.domain.render import renderfiles
from cutty.filesystem.path import Path


PathLoader = Callable[[Path], Iterator[Path]]


class RenderService:
    """Service for rendering a template."""

    def __init__(
        self,
        *,
        renderbind: RenderBinder,
        loadconfig: TemplateConfigLoader,
        loadrenderer: RendererLoader,
        loadpaths: PathLoader,
        storefile: FileStorage
    ):
        """Initialize."""
        self.loadconfig = loadconfig
        self.loadrenderer = loadrenderer
        self.loadpaths = loadpaths
        self.renderbind = renderbind
        self.storefile = storefile

    def render(self, path: Path) -> None:
        """Render the template at the given path."""
        config = self.loadconfig(path)
        render = self.loadrenderer(path, config.settings)
        bindings = self.renderbind(render, config.variables)
        paths = self.loadpaths(path)
        for file in renderfiles(paths, render, bindings):
            self.storefile(file)
