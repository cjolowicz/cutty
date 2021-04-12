"""Provider for Mercurial repositories."""
from cutty.repositories2.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories2.domain.providers import remoteproviderfactory


hgproviderfactory = remoteproviderfactory(fetch=[hgfetcher])
