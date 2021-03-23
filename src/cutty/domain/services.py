"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence

from cutty.domain.binders import RenderBinder
from cutty.domain.config import Config
from cutty.domain.files import FileStorage
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor
from cutty.domain.hooks import registerhook
from cutty.domain.render import Renderer
from cutty.domain.renderfiles import renderfiles
from cutty.domain.variables import Variable
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

    _render(renderbind, render, config.variables, hooks, executehook, paths, storefile)


def _render(
    renderbind: RenderBinder,
    render: Renderer,
    variables: Sequence[Variable],
    hooks: Iterator[Hook],
    executehook: HookExecutor,
    paths: Iterator[Path],
    storefile: FileStorage,
) -> None:
    bus = Bus()
    bindings = renderbind(render, variables)

    for hook in hooks:
        registerhook(hook, render, bindings, executehook, bus)

    for file in renderfiles(paths, render, bindings, bus):
        storefile(file)
