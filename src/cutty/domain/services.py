"""Domain services."""
from cutty.domain.binders import Binder
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
        bind: Binder,
        configloader: TemplateConfigLoader,
        rendererfactory: RendererFactory,
        fileloader: FileLoader,
        storage: FileStorage
    ):
        """Initialize."""
        self.configloader = configloader
        self.rendererfactory = rendererfactory
        self.fileloader = fileloader
        self.bind = bind
        self.storage = storage

    def render(self, path: Path) -> None:
        """Render the template at the given path."""
        config = self.configloader.load(path)
        render = self.rendererfactory.create(path, settings=config.settings)
        bindings = self.bind(config.variables, render=render)
        files = self.fileloader.load(path)

        for file in renderfiles(files, render=render, bindings=bindings):
            self.storage.store(file)
