"""Domain services."""
from cutty.domain.binders import Binder
from cutty.domain.files import FileLoader
from cutty.domain.files import FileStorage
from cutty.domain.loader import RendererFactory
from cutty.domain.loader import TemplateConfigLoader
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateRenderer
from cutty.filesystem.path import Path


class RenderService:
    """Service for rendering a template."""

    def __init__(
        self,
        *,
        binder: Binder,
        configloader: TemplateConfigLoader,
        rendererfactory: RendererFactory,
        fileloader: FileLoader,
        storage: FileStorage
    ):
        """Initialize."""
        self.configloader = configloader
        self.rendererfactory = rendererfactory
        self.fileloader = fileloader
        self.renderer = TemplateRenderer(
            binder=binder,
            storage=storage,
        )

    def render(self, path: Path) -> None:
        """Render the template at the given path."""
        config = self.configloader.load(path)
        renderer = self.rendererfactory.create(path, settings=config.settings)
        files = self.fileloader.load(path)
        template = Template(config=config, files=files, renderer=renderer)
        self.renderer.render(template)
