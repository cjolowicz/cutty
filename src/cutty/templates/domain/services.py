"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.binders import RenderBinder
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles


ConfigLoader = Callable[[Path], Config]
PathLoader = Callable[[Path, Config], Iterator[Path]]
RendererLoader = Callable[[Path, Config], Renderer]


def render(
    path: Path,
    *,
    renderbind: RenderBinder,
    loadconfig: ConfigLoader,
    loadrenderer: RendererLoader,
    loadpaths: PathLoader,
) -> Iterator[File]:
    """Render the template at the given path."""
    config = loadconfig(path)
    render = loadrenderer(path, config)
    paths = loadpaths(path, config)

    bindings = renderbind(render, config.variables)
    return renderfiles(paths, render, bindings)
