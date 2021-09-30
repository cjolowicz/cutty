"""Loading templates."""
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
class TemplateMetadata:
    """Metadata for a project template."""

    location: str
    checkout: Optional[str]
    directory: Optional[pathlib.PurePosixPath]
    name: str
    revision: Optional[Revision]


@dataclass
class Template:
    """Project template."""

    metadata: TemplateMetadata
    root: Path


def loadtemplate(
    template: str, checkout: Optional[str], directory: Optional[pathlib.PurePosixPath]
) -> Repository:
    """Load a template repository."""
    cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
    repositoryprovider = getdefaultrepositoryprovider(cachedir)
    return repositoryprovider(
        template,
        revision=checkout,
        directory=(PurePath(*directory.parts) if directory is not None else None),
    )
