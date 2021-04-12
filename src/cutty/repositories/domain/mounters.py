"""Mounting filesystems."""
import pathlib
from collections.abc import Callable
from typing import Optional

from cutty.filesystems.domain.filesystem import Filesystem
from cutty.repositories.domain.revisions import Revision


Mounter = Callable[[pathlib.Path, Optional[Revision]], Filesystem]


def unversioned_mounter(filesystem: Callable[[pathlib.Path], Filesystem]) -> Mounter:
    """Return a mounter that raises when a revision is passed."""

    def _mount(storage: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
        if revision is not None:
            raise RuntimeError(f"filesystem does not support revisions, got {revision}")
        return filesystem(storage)

    return _mount
