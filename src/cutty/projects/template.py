"""Loading templates."""
from __future__ import annotations

import pathlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

import platformdirs

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.packages.adapters.registry import defaultproviderfactories
from cutty.packages.adapters.storage import getdefaultproviderstore
from cutty.packages.domain.registry import ProviderRegistry
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.revisions import Revision


@dataclass
class TemplateProvider:
    """Provider of project templates."""

    registry: ProviderRegistry

    @classmethod
    def create(cls) -> TemplateProvider:
        """Create the template provider."""
        cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
        registry = ProviderRegistry(
            getdefaultproviderstore(cachedir), defaultproviderfactories
        )

        return cls(registry)

    def provide(
        self, location: str, directory: Optional[pathlib.Path]
    ) -> TemplateRepository:
        """Load a template repository."""
        repository = self.registry.getrepository(location)

        return TemplateRepository(repository, location, directory)


@dataclass
class TemplateRepository:
    """Repository of project templates."""

    repository: PackageRepository
    location: str
    directory: Optional[pathlib.Path]

    @contextmanager
    def get(self, revision: Optional[str]) -> Iterator[Template]:
        """Load a project template."""
        with self.repository.get(revision) as package:
            if self.directory is not None:
                package = package.descend(PurePath(*self.directory.parts))

            metadata = Template.Metadata(
                self.location,
                self.directory,
                package.name,
                package.revision,
                package.commit,
                package.message,
            )

            yield Template(metadata, package.tree)

    def getparentrevision(self, revision: Optional[str]) -> Optional[str]:
        """Return the parent revision, if any."""
        return self.repository.getparentrevision(revision)


@dataclass
class Template:
    """Project template."""

    @dataclass
    class Metadata:
        """Metadata for a project template."""

        location: str
        directory: Optional[pathlib.Path]
        name: str
        revision: Optional[Revision]
        commit: Optional[str] = None
        message: Optional[str] = None

    metadata: Metadata
    root: Path
