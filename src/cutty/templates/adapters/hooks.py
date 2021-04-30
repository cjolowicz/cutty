"""Hooks for rendering templates."""
from collections import ChainMap
from collections.abc import Iterable
from collections.abc import Sequence
from itertools import chain
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry
from cutty.templates.domain.binders import Binder
from cutty.templates.domain.binders import renderbind as binders_renderbind
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.render import RenderRegistry
from cutty.templates.domain.services import ConfigLoader
from cutty.templates.domain.services import PathIterable
from cutty.templates.domain.services import RendererFactory
from cutty.templates.domain.variables import Variable


@hook(firstresult=True)
def loadtemplateconfig(path: Path) -> Optional[Config]:
    """Load the template configuration."""


def getconfigloader(registry: Registry) -> ConfigLoader:
    """Return a loader for template configurations."""
    dispatch = registry.bind(loadtemplateconfig)

    def _configloader(path: Path) -> Config:
        result = dispatch(path)
        assert result is not None  # noqa: S101
        return result

    return _configloader


@hook
def getrenderers(path: Path, config: Config) -> RenderRegistry:
    """Return renderers."""


@implements(getrenderers)
def getrenderers_impl(path: Path, config: Config) -> RenderRegistry:
    """Return the default renderers."""
    return defaultrenderregistry


def getrendererfactory(registry: Registry) -> RendererFactory:
    """Return a hook-based renderer factory."""
    dispatch = registry.bind(getrenderers)
    registry.register(getrenderers_impl)

    def _wrapper(path: Path, config: Config) -> Renderer:
        renderregistries: list[RenderRegistry] = dispatch(path, config)
        renderregistry = ChainMap(*renderregistries)
        return createrenderer(renderregistry)

    return _wrapper


@hook
def getpaths(path: Path, config: Config) -> Iterable[Path]:
    """Iterate over the files and directories to be rendered."""


def getpathiterable(registry: Registry) -> PathIterable:
    """Return a path iterable."""
    dispatch = registry.bind(getpaths)

    def _wrapper(path: Path, config: Config) -> Iterable[Path]:
        iterables: list[Iterable[Path]] = dispatch(path, config)
        return chain(*iterables)

    return _wrapper


@hook(firstresult=True)
def getbinder() -> Binder:
    """Return a function that binds variables."""


@hook(firstresult=True)
def renderbind(render: Renderer, variables: Sequence[Variable]) -> Sequence[Binding]:
    """Render and bind variables."""


def getrenderbind(registry: Registry) -> None:
    dispatch = registry.bind(renderbind)
    getbinder = registry.bind(getbinder)

    @registry.register
    @implements(renderbind)
    def renderbind_impl(
        render: Renderer, variables: Sequence[Variable]
    ) -> Sequence[Binding]:
        """Successively render and bind variables."""
        binder = getbinder()
        return binders_renderbind(render, binder, variables)
