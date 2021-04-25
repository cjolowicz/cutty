"""Hook specifications."""
from pathlib import Path
from typing import Optional

from cutty.plugins.markers import hookspecification
from cutty.repositories.domain.providers import ProviderStore


@hookspecification(firstresult=True)
def getrepositorystorage(provider: str, url: str) -> Optional[Path]:
    """Return a storage location for a repository.

    Args:
        provider: The provider, such as ``git`` or ``zip``
        url: The URL of the repository

    Returns:
        A storage location on the local filesystem, or None.
    """
