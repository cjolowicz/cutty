"""Loading templates."""
from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Optional

import platformdirs

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision


@dataclass
class Template:
    """Project template."""

    @dataclass
    class Metadata:
        """Metadata for a project template."""

        location: str
        checkout: Optional[str]
        directory: Optional[pathlib.PurePosixPath]
        name: str
        revision: Optional[Revision]

    metadata: Metadata
    root: Path

    @classmethod
    def load(
        cls,
        template: str,
        checkout: Optional[str],
        directory: Optional[pathlib.PurePosixPath],
    ) -> Template:
        """Load a project template."""
        cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
        repositoryprovider = getdefaultrepositoryprovider(cachedir)
        repository = repositoryprovider(
            template,
            revision=checkout,
            directory=(PurePath(*directory.parts) if directory is not None else None),
        )
        return _createtemplate(template, checkout, directory, repository)


TemplateMetadata = Template.Metadata


def _createtemplate(
    template: str,
    checkout: Optional[str],
    directory: Optional[pathlib.PurePosixPath],
    repository: Repository,
) -> Template:
    metadata = TemplateMetadata(
        template, checkout, directory, repository.name, repository.revision
    )
    return Template(metadata, repository.path)
