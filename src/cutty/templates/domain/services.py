"""Domain services."""
from collections.abc import Callable
from collections.abc import Iterator

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.binders import RenderingBinder
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.render import RenderRegistry
from cutty.templates.domain.renderfiles import renderfiles


ConfigLoader = Callable[[Path], Config]
PathIterator = Callable[[Path, Config], Iterator[Path]]
RendererRegistrar = Callable[[Path, Config], RenderRegistry]


def render(
    path: Path,
    *,
    renderbind: RenderingBinder,
    loadconfig: ConfigLoader,
    registerrenderers: RendererRegistrar,
    iterpaths: PathIterator,
) -> Iterator[File]:
    """Render the template at the given path."""
    config = loadconfig(path)
    renderregistry = registerrenderers(path, config)
    render = createrenderer({**defaultrenderregistry, **renderregistry})
    paths = iterpaths(path, config)

    bindings = renderbind(render, config.variables)
    return renderfiles(paths, render, bindings)
