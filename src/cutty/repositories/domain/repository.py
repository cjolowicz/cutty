"""Repository."""
from dataclasses import dataclass
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.pathfs import PathFilesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.domain.revisions import Revision


@dataclass
class Repository:
    """A repository."""

    name: str
    path: Path
    revision: Optional[Revision]


def descend(repository: Repository, directory: PurePath) -> Repository:
    """Return the subrepository located in the given directory."""
    path = repository.path.joinpath(*directory.parts)
    return Repository(
        directory.name,
        Path(filesystem=PathFilesystem(path)),
        repository.revision,
    )
