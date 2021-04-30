"""Hooks for rendering templates."""
from collections import ChainMap
from collections.abc import Iterable
from itertools import chain
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.render import RenderRegistry
from cutty.templates.domain.services import ConfigLoader
from cutty.templates.domain.services import PathIterable
from cutty.templates.domain.services import RendererRegistrar


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


def getrendererregistrar(registry: Registry) -> RendererRegistrar:
    """Return a registrar for renderers."""
    dispatch = registry.bind(getrenderers)
    registry.register(getrenderers_impl)

    def _wrapper(path: Path, config: Config) -> RenderRegistry:
        registries: list[RenderRegistry] = dispatch(path, config)
        return ChainMap(*registries)

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
