"""Provider registry."""
import shutil

from cutty.repositories.adapters.providers.disk import diskprovider
from cutty.repositories.adapters.providers.git import gitproviderfactory
from cutty.repositories.adapters.providers.git import localgitprovider
from cutty.repositories.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories.adapters.providers.zip import localzipprovider
from cutty.repositories.adapters.providers.zip import zipproviderfactory
from cutty.repositories.domain.providers import asproviderfactory2
from cutty.repositories.domain.providers import constproviderfactory as factory
from cutty.repositories.domain.providers import registerproviderfactories2


_defaultproviderregistry = {
    "localzip": factory(localzipprovider),
    "localgit": factory(localgitprovider),
    "local": factory(diskprovider),
    "zip": asproviderfactory2(zipproviderfactory),
    "git": asproviderfactory2(gitproviderfactory),
}

if shutil.which("hg") is not None:  # pragma: no cover
    _defaultproviderregistry["hg"] = asproviderfactory2(hgproviderfactory)

defaultproviderregistry = registerproviderfactories2(**_defaultproviderregistry)
