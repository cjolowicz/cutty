"""Loading templates."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Optional

import platformdirs

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.packages.adapters.storage import getdefaultpackageprovider
from cutty.packages.domain.revisions import Revision


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

    @classmethod
    def load(
        cls,
        template: str,
        revision: Optional[str],
        directory: Optional[pathlib.Path],
    ) -> Template:
        """Load a project template."""
        cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
        packageprovider = getdefaultpackageprovider(cachedir)
        package = packageprovider(
            template,
            revision=revision,
            directory=(PurePath(*directory.parts) if directory is not None else None),
        )

        metadata = cls.Metadata(template, directory, package.name, package.revision)
        return cls(metadata, package.path)
