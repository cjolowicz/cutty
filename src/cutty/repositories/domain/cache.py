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

    def __init__(self, path: pathlib.Path, providers: Iterable[Provider]):
        """Initialize."""
        self.backend = Backend(path)
        self.providers = tuple(providers)

    def get(
        self,
        url: URL,
        *,
        revision: Optional[str] = None,
        providers: Iterable[str] = (),
        wantupdate: bool = True,
    ) -> Path:
        """Load a tree from the cache."""
        provider = next(
            provider
            for provider in self.providers
            if (not providers or provider.name in providers) and provider.matches(url)
        )
        entry = self.backend.get(url, provider.name)

        if entry.provider != provider.name:
            # The repository was previously downloaded using a different
            # provider.
            provider = next(
                provider
                for provider in self.providers
                if provider.name == entry.provider and provider.matches(url)
            )

        if not provider.exists(url, entry.path):
            provider.download(url, entry.path)
        elif wantupdate:
            provider.update(url, entry.path)

        return provider.resolve(url, entry.path, revision)
