"""Provider registry."""
import shutil

from cutty.packages.adapters.providers.disk import diskprovider
from cutty.packages.adapters.providers.git import gitproviderfactory
from cutty.packages.adapters.providers.git import localgitprovider
from cutty.packages.adapters.providers.mercurial import hgproviderfactory
from cutty.packages.adapters.providers.zip import localzipprovider
from cutty.packages.adapters.providers.zip import zipproviderfactory
from cutty.packages.domain.providers import ConstProviderFactory as Factory


defaultproviderfactories = [
    Factory(localzipprovider),
    Factory(localgitprovider),
    Factory(diskprovider),
    zipproviderfactory,
    gitproviderfactory,
]

if shutil.which("hg") is not None:  # pragma: no cover
    defaultproviderfactories.append(hgproviderfactory)
