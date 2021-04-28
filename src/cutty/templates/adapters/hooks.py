"""Hooks for rendering templates."""
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.registry import Registry
from cutty.templates.domain.config import Config
from cutty.templates.domain.services import ConfigLoader


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
