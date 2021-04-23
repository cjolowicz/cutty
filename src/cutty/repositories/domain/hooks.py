"""Hook specifications."""
from typing import Optional

from cutty.plugins.markers import hookspecification
from cutty.repositories.domain.providers import ProviderStore


@hookspecification(firstresult=True)
def providerstore() -> Optional[ProviderStore]:
    """Return a provider store."""
