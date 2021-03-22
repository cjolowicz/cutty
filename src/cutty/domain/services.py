"""Domain services."""
from cutty.domain.binders import RenderBinder
from cutty.domain.files import FileLoader
from cutty.domain.files import FileStorage
from cutty.domain.loader import RendererFactory
from cutty.domain.loader import TemplateConfigLoader
from cutty.domain.render import renderfiles
from cutty.filesystem.path import Path


class RenderService:
    """Service for rendering a template."""

    def __init__(
        self,
        *,
        renderbind: RenderBinder,
        configloader: TemplateConfigLoader,
        rendererfactory: RendererFactory,
        loadfiles: FileLoader,
        storefile: FileStorage
    ):
        """Initialize."""
        self.configloader = configloader
        self.rendererfactory = rendererfactory
        self.loadfiles = loadfiles
        self.renderbind = renderbind
        self.storefile = storefile

    def render(self, path: Path) -> None:
        """Render the template at the given path."""
        config = self.configloader.load(path)
        render = self.rendererfactory.create(path, settings=config.settings)
        bindings = self.renderbind(render, config.variables)
        files = self.loadfiles(path)

        for file in renderfiles(files, render=render, bindings=bindings):
            self.storefile(file)
