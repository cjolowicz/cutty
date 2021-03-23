"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator

from cutty.domain.binders import RenderBinder
from cutty.domain.config import Config
from cutty.domain.files import FileStorage
from cutty.domain.render import Renderer
from cutty.domain.render import renderfiles
from cutty.filesystem.path import Path
from cutty.util.bus import Bus


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
    storefile: FileStorage
) -> None:
    """Render the template at the given path."""
    config = loadconfig(path)
    render = loadrenderer(path, config)
    paths = loadpaths(path, config)
    bindings = renderbind(render, config.variables)
    bus = Bus()

    for file in renderfiles(paths, render, bindings, bus):
        storefile(file)
