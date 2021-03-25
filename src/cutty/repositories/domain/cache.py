"""Repository cache."""
import pathlib
from collections.abc import Container
from collections.abc import Iterable
from typing import Optional

from yarl import URL

from cutty.filesystem.domain.path import Path
from cutty.repositories.domain.backends import Backend
from cutty.repositories.domain.repositories import Repository


class Cache:
    """Repository cache."""

    def __init__(self, path: pathlib.Path, providers: Iterable[type[Repository]]):
        """Initialize."""
        self.backend = Backend(path)
        self.providers = tuple(providers)

    def getprovider(self, url: URL, types: Container[str] = ()) -> type[Repository]:
        """Return a repository type for the given URL and type names."""
        return next(
            provider
            for provider in self.providers
            if (not types or provider.type in types) and provider.supports(url)
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
        provider = self.getprovider(url, set(providers))
        entry = self.backend.get(url, provider.type)

        if entry.provider != provider.type:
            # The repository was downloaded using a different provider.
            provider = self.getprovider(url, [entry.provider])

        repository = provider(url, entry.path)

        if not repository.exists():
            repository.download()
        elif wantupdate:
            repository.update()

        return repository.resolve(revision)
