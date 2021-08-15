"""Provider for Mercurial repositories."""
from cutty.repositories.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories.domain.providers import remoteproviderfactory2


hgproviderfactory = remoteproviderfactory2(fetch=[hgfetcher])
