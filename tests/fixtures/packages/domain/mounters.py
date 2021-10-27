"""Fixtures for cutty.packages.domain.mounters."""
import json
import pathlib
from typing import Optional

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.domain.mounters import asmounter2
from cutty.packages.domain.mounters import Mounter
from cutty.packages.domain.mounters import Mounter2
from cutty.packages.domain.mounters import unversioned_mounter
from cutty.packages.domain.mounters import unversioned_mounter2
from cutty.packages.domain.revisions import Revision


@pytest.fixture
def diskmounter() -> Mounter:
    """Fixture with an unversioned disk filesystem mounter."""
    return unversioned_mounter(DiskFilesystem)


@pytest.fixture
def diskmounter2() -> Mounter2:
    """Fixture with an unversioned disk filesystem mounter."""
    return unversioned_mounter2(DiskFilesystem)


@pytest.fixture
def jsonmounter() -> Mounter:
    """Mount a versioned dict filesystem read from JSON."""

    def _(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
        text = path.read_text()
        data = json.loads(text)
        return DictFilesystem(data[revision] if revision is not None else data)

    return _


@pytest.fixture
def jsonmounter2(jsonmounter: Mounter) -> Mounter2:
    """Mount a versioned dict filesystem read from JSON."""
    return asmounter2(jsonmounter)
