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
from cutty.packages.adapters.storage import getdefaultpackageprovider
from cutty.packages.domain.revisions import Revision


class TemplateRepository:
    """Repository of project templates."""

    @contextmanager
    def get(
        self,
        template: str,
        revision: Optional[str],
        directory: Optional[pathlib.Path],
    ) -> Iterator[Template]:
        """Load a project template."""
        cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
        packageprovider = getdefaultpackageprovider(cachedir)
        repository = packageprovider.getrepository(template)

        with repository.get(revision) as package:
            if directory is not None:
                package = package.descend(PurePath(*directory.parts))

            metadata = Template.Metadata(
                template, directory, package.name, package.revision
            )

            yield Template(metadata, package.tree)


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

    metadata: Metadata
    root: Path
