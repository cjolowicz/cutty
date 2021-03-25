"""Repository cache."""
import contextlib
import pathlib
from collections.abc import Container
from collections.abc import Iterable
from typing import Optional

from yarl import URL

from cutty.filesystem.domain.path import Path
from cutty.repositories.domain.backends import Backend
from cutty.repositories.domain.repositories import LocalRepository
from cutty.repositories.domain.repositories import Repository


class Cache:
    """Repository cache."""

    def __init__(
        self,
        path: pathlib.Path,
        *,
        local: Iterable[type[LocalRepository]],
        remote: Iterable[type[Repository]],
    ):
        """Initialize."""
        self.backend = Backend(path)
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
        return repository.resolve(revision)

    def getremote(
        self,
        url: URL,
        *,
        revision: Optional[str] = None,
        providers: Container[str],
        wantupdate: bool = True,
    ) -> Path:
        """Load a tree from the cache."""
        entry = self.backend.get(url)

        if entry is not None:
            providers = {entry.provider}

        provider = next(
            provider
            for provider in self.remoteproviders
            if (not providers or provider.type in providers) and provider.supports(url)
        )

        if entry is None:
            entry = self.backend.allocate(url, provider.type)

        repository = provider(url, entry.path)

        if not repository.exists():
            repository.download()
        elif wantupdate:
            repository.update()

        return repository.resolve(revision)
