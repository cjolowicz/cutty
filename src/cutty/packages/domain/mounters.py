"""Mounting filesystems."""
import pathlib
from collections.abc import Callable
from collections.abc import Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.domain.revisions import Revision


Mounter = Callable[[pathlib.Path, Optional[Revision]], Filesystem]
Mounter2 = Callable[
    [pathlib.Path, Optional[Revision]], AbstractContextManager[Filesystem]
]


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


def asmounter2(mount: Mounter) -> Mounter2:
    """Convert `Mounter` to `Mounter2`."""

    @contextmanager
    def _(path: pathlib.Path, revision: Optional[Revision]) -> Iterator[Filesystem]:
        yield mount(path, revision)

    return _
