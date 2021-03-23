"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.binders import RenderBinder
from cutty.domain.bindings import Binding
from cutty.domain.config import TemplateConfig
from cutty.domain.files import FileStorage
from cutty.domain.render import Renderer
from cutty.domain.render import renderfiles
from cutty.filesystem.path import Path


TemplateConfigLoader = Callable[[Path], TemplateConfig]
PathLoader = Callable[[Path, TemplateConfig], Iterator[Path]]
RendererLoader = Callable[[Path, Sequence[Binding]], Renderer]


def render(
    path: Path,
    *,
    renderbind: RenderBinder,
    loadconfig: TemplateConfigLoader,
    loadrenderer: RendererLoader,
    loadpaths: PathLoader,
    storefile: FileStorage
) -> None:
    """Render the template at the given path."""
    config = loadconfig(path)
    render = loadrenderer(path, config.settings)
    bindings = renderbind(render, config.variables)
    paths = loadpaths(path, config)
    for file in renderfiles(paths, render, bindings):
        storefile(file)
