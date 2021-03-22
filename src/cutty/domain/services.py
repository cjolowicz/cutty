"""Domain services."""
from cutty.domain.binders import Binder
from cutty.domain.files import FileLoader
from cutty.domain.files import FileStorage
from cutty.domain.loader import RendererFactory
from cutty.domain.loader import TemplateConfigLoader
from cutty.domain.loader import TemplateLoader
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
        self.loader = TemplateLoader(
            configloader=configloader,
            rendererfactory=rendererfactory,
            fileloader=fileloader,
        )
        self.renderer = TemplateRenderer(
            binder=binder,
            storage=storage,
        )

    def render(self, path: Path) -> None:
        """Render the template at the given path."""
        template = self.loader.load(path)
        self.renderer.render(template)
