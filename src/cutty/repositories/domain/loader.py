"""Repository loader."""
import contextlib
import pathlib
from collections.abc import Container
from collections.abc import Iterable
from typing import Optional

from yarl import URL

from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.cache import RepositoryCache
from cutty.repositories.domain.repositories import LocalRepository
from cutty.repositories.domain.repositories import Repository


class RepositoryLoader:
    """Repository loader."""

    def __init__(
        self,
        *,
        cachedir: pathlib.Path,
        local: Iterable[type[LocalRepository]],
        remote: Iterable[type[Repository]],
    ):
        """Initialize."""
        self.cache = RepositoryCache(cachedir)
        self.localproviders = tuple(local)
        self.remoteproviders = tuple(remote)

    def get(
        self,
        location: str,
        *,
        revision: Optional[str] = None,
        providers: Iterable[str] = (),
        wantupdate: bool = True,
    ) -> Path:
        """Load a tree."""
        providers = set(providers)
        with contextlib.suppress(StopIteration):
            return self.getlocal(
                pathlib.Path(location),
                revision=revision,
                providers=providers,
            )

        with contextlib.suppress(StopIteration):
            return self.getremote(
                URL(location),
                revision=revision,
                providers=providers,
                wantupdate=wantupdate,
            )

        raise RuntimeError(f"could not find repository provider for {location}")

    def getlocal(
        self,
        path: pathlib.Path,
        *,
        revision: Optional[str] = None,
        providers: Container[str],
    ) -> Path:
        """Load a tree from the local filesystem."""
        provider = next(
            provider
            for provider in self.localproviders
            if (not providers or provider.type in providers) and provider.supports(path)
        )

        repository = provider(path)
        filesystem = repository.resolve(revision)
        return Path(filesystem=filesystem)

    def getremote(
        self,
        url: URL,
        *,
        revision: Optional[str] = None,
        providers: Container[str],
        wantupdate: bool = True,
    ) -> Path:
        """Load a tree from the cache."""
        entry = self.cache.get(url)

        if entry is not None:
            providers = {entry.provider}

        provider = next(
            provider
            for provider in self.remoteproviders
            if (not providers or provider.type in providers) and provider.supports(url)
        )

        if entry is None:
            entry = self.cache.allocate(url, provider.type)

        repository = provider(url, entry.path)

        if not repository.exists():
            repository.download()
        elif wantupdate:
            repository.update()

        filesystem = repository.resolve(revision)
        return Path(filesystem=filesystem)
