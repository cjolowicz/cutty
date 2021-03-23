"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator

from cutty.domain.binders import RenderBinder
from cutty.domain.config import Config
from cutty.domain.files import FileStorage
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor
from cutty.domain.hooks import registerhook
from cutty.domain.render import Renderer
from cutty.domain.render import renderfiles
from cutty.filesystem.path import Path
from cutty.util.bus import Bus


ConfigLoader = Callable[[Path], Config]
PathLoader = Callable[[Path, Config], Iterator[Path]]
HookLoader = Callable[[Path, Config], Iterator[Hook]]
RendererLoader = Callable[[Path, Config], Renderer]


def render(
    path: Path,
    *,
    renderbind: RenderBinder,
    loadconfig: ConfigLoader,
    loadrenderer: RendererLoader,
    loadpaths: PathLoader,
    loadhooks: HookLoader,
    storefile: FileStorage,
    executehook: HookExecutor,
) -> None:
    """Render the template at the given path."""
    config = loadconfig(path)
    render = loadrenderer(path, config)
    paths = loadpaths(path, config)
    hooks = loadhooks(path, config)
    bindings = renderbind(render, config.variables)
    bus = Bus()

    for hook in hooks:
        registerhook(hook, render, bindings, executehook, bus)

    for file in renderfiles(paths, render, bindings, bus):
        storefile(file)
