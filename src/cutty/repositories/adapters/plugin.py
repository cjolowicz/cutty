"""Hook implementations."""
from pathlib import Path

import appdirs

from cutty.plugins.markers import hookimplementation
from cutty.repositories.adapters.storage import asproviderstore
from cutty.repositories.adapters.storage import RepositoryStorage
from cutty.repositories.domain.providers import ProviderStore


@hookimplementation(trylast=True)
def providerstore() -> ProviderStore:
    """Return a provider store."""
    cachedir = Path(appdirs.user_cache_dir("cutty"))
    repositorystorage = RepositoryStorage(cachedir)
    return asproviderstore(repositorystorage)
