"""Repository cache."""
import pathlib
from collections.abc import Iterable
from typing import Optional

from yarl import URL

from cutty.filesystem.path import Path
from cutty.repositories.domain.backends import Backend
from cutty.repositories.domain.providers import Provider


class Cache:
    """Repository cache."""

    def __init__(self, path: pathlib.Path, providers: Iterable[type[Provider]]):
        """Initialize."""
        self.backend = Backend(path)
        self.providers = tuple(providers)

    def getprovider(self, url: URL, names: Iterable[str]) -> type[Provider]:
        """Return a repository provider that matches the URL and names."""
        return next(
            provider
            for provider in self.providers
            if (not names or provider.name in names) and provider.matches(url)
        )

    def get(
        self,
        url: URL,
        *,
        revision: Optional[str] = None,
        providers: Iterable[str] = (),
        wantupdate: bool = True,
    ) -> Path:
        """Load a tree from the cache."""
        provider = self.getprovider(url, providers)
        entry = self.backend.get(url, provider.name)

        if entry.provider != provider.name:
            # The repository was previously downloaded using a different
            # provider.
            provider = self.getprovider(url, [entry.provider])

        repository = provider(url, entry.path)

        if not repository.exists():
            repository.download()
        elif wantupdate:
            repository.update()

        return repository.resolve(revision)
