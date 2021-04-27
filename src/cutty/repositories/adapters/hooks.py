"""Hooks."""
from collections import ChainMap
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import appdirs
from yarl import URL

from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry
from cutty.repositories.adapters.registry import defaultproviderregistry
from cutty.repositories.adapters.storage import RepositoryStorage
from cutty.repositories.domain.providers import ProviderRegistry
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.stores import Store


@hook(firstresult=True)
def getrepositorystorage(provider: str, url: str) -> Optional[Path]:
    """Return a storage location for a repository.

    Args:
        provider: The provider, such as ``git`` or ``zip``
        url: The URL of the repository

    Returns:
        A storage location on the local filesystem, or None.
    """  # noqa: DAR202


def getrepositorystorage_impl(projectname: str) -> Callable[[str, str], Optional[Path]]:
    """Implement the ``getrepositorystorage`` hook."""
    cachedir = Path(appdirs.user_cache_dir(projectname))
    storage = RepositoryStorage(cachedir)

    @implements(getrepositorystorage)
    def getrepositorystorage_(provider: str, url: str) -> Optional[Path]:
        """Return a storage location for a repository."""
        url_ = URL(url)
        record = storage.get(url_, provider=provider)
        if record is None:
            record = storage.allocate(url_, provider=provider)
        return record.path

    return getrepositorystorage_


def getproviderstore(registry: Registry, projectname: str) -> ProviderStore:
    """Return a provider store."""
    dispatch = registry.bind(getrepositorystorage)
    implementation = getrepositorystorage_impl(projectname)
    registry.register(implementation)

    def _providerstore(provider: str) -> Store:
        def _store(url: URL) -> Path:
            result = dispatch(provider, str(url))
            assert result is not None  # noqa: S101
            return result

        return _store

    return _providerstore


@hook
def getproviders() -> ProviderRegistry:
    """Return repository providers."""


@implements(getproviders)
def getproviders_impl() -> ProviderRegistry:
    """Return the default repository providers."""
    return defaultproviderregistry


def getproviderregistry(registry: Registry) -> ProviderRegistry:
    """Return the repository providers."""
    dispatch = registry.bind(getproviders)
    registry.register(getproviders_impl)
    registries: list[ProviderRegistry] = dispatch()

    # A ChainMap preserves the LIFO semantics from the hook dispatch. If two
    # implementations return providers under the same provider name, the later
    # one overrides the earlier one. This allows plugins to override providers
    # we supply by default, such as `git` and `hg`.

    return ChainMap(*registries)
