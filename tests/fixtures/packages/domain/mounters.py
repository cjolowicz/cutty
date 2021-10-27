"""Fixtures for cutty.packages.domain.mounters."""
import json
import pathlib
from collections.abc import Iterator
from typing import Optional

import pytest

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.mounters import unversioned_mounter
from cutty.packages.domain.revisions import Revision


@pytest.fixture
def diskmounter2() -> Mounter:
    """Fixture with an unversioned disk filesystem mounter."""
    return unversioned_mounter(DiskFilesystem)


@pytest.fixture
def jsonmounter2() -> Mounter:
    """Mount a versioned dict filesystem read from JSON."""

    @contextmanager
    def _(path: pathlib.Path, revision: Optional[Revision]) -> Iterator[Filesystem]:
        text = path.read_text()
        data = json.loads(text)
        yield DictFilesystem(data[revision] if revision is not None else data)

    return _
