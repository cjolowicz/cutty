"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterable

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.binders import RenderingBinder
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles


ConfigLoader = Callable[[Path], Config]
PathIterable = Callable[[Path, Config], Iterable[Path]]
RendererFactory = Callable[[Path, Config], Renderer]


def render(
    path: Path,
    *,
    renderbind: RenderingBinder,
    loadconfig: ConfigLoader,
    getrenderer: RendererFactory,
    getpaths: PathIterable,
) -> Iterable[File]:
    """Render the template at the given path."""
    config = loadconfig(path)
    render = getrenderer(path, config)
    paths = getpaths(path, config)

    bindings = renderbind(render, config.variables)
    return renderfiles(paths, render, bindings)
