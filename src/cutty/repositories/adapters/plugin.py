"""Hook implementations."""
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import appdirs
from yarl import URL

from cutty.plugins.markers import hookimplementation
from cutty.repositories.adapters.storage import asproviderstore
from cutty.repositories.adapters.storage import RepositoryStorage
from cutty.repositories.domain.providers import ProviderStore


def getrepositorystorageimpl(name: str) -> Callable[[str, str], Optional[Path]]:
    """Implement the ``getrepositorystorage`` hook."""

    cachedir = Path(appdirs.user_cache_dir(name))
    repositorystorage = RepositoryStorage(cachedir)
    providerstore = asproviderstore(repositorystorage)

    @hookimplementation(trylast=True)
    def getrepositorystorage(provider: str, url: str) -> Optional[Path]:
        """Return a storage location for a repository."""
        store = providerstore(provider)
        return store(URL(url))

    return getrepositorystorage
