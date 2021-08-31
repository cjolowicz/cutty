"""Mounting filesystems."""
import pathlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

from cutty.errors import CuttyError
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.repositories.domain.revisions import Revision


Mounter = Callable[[pathlib.Path, Optional[Revision]], Filesystem]


@dataclass
class UnsupportedRevisionError(CuttyError):
    """The filesystem does not support revisions."""

    revision: Revision


def unversioned_mounter(filesystem: Callable[[pathlib.Path], Filesystem]) -> Mounter:
    """Return a mounter that raises when a revision is passed."""

    def _mount(storage: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
        if revision is not None:
            raise UnsupportedRevisionError(revision)
        return filesystem(storage)

    return _mount
