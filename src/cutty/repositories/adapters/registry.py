"""Provider registry."""
import shutil

from cutty.repositories.adapters.providers.disk import diskprovider
from cutty.repositories.adapters.providers.git import gitproviderfactory
from cutty.repositories.adapters.providers.git import localgitprovider
from cutty.repositories.adapters.providers.mercurial import hgproviderfactory
from cutty.repositories.adapters.providers.zip import localzipprovider
from cutty.repositories.adapters.providers.zip import zipproviderfactory
from cutty.repositories.domain.providers import asprovider2
from cutty.repositories.domain.providers import constproviderfactory as factory
from cutty.repositories.domain.providers import registerproviderfactories
from cutty.repositories.domain.providers import registerproviderfactories2


_defaultproviderregistry2 = {
    "localzip": factory(asprovider2(localzipprovider)),
    "localgit": factory(asprovider2(localgitprovider)),
    "local": factory(asprovider2(diskprovider)),
}

defaultproviderregistry = registerproviderfactories2(**_defaultproviderregistry2)

_defaultproviderregistry = {
    "zip": zipproviderfactory,
    "git": gitproviderfactory,
}

if shutil.which("hg") is not None:  # pragma: no cover
    _defaultproviderregistry["hg"] = hgproviderfactory

defaultproviderregistry = registerproviderfactories(
    defaultproviderregistry, **_defaultproviderregistry
)
