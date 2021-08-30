"""Provider registry."""
import shutil

from cutty.repositories.adapters.providers.disk import diskprovider
from cutty.repositories.adapters.providers.git import gitproviderfactory
from cutty.repositories.adapters.providers.git import localgitprovider
from cutty.repositories.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories.adapters.providers.zip import localzipprovider
from cutty.repositories.adapters.providers.zip import zipproviderfactory
from cutty.repositories.domain.providers import constproviderfactory as factory


defaultproviderfactories2 = [
    factory(localzipprovider),
    factory(localgitprovider),
    factory(diskprovider),
    zipproviderfactory,
    gitproviderfactory,
]

if shutil.which("hg") is not None:  # pragma: no cover
    defaultproviderfactories2.append(hgproviderfactory)
