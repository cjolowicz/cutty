"""Unit tests for cutty.repositories2.domain.mounters."""
from pathlib import Path

import pytest

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.repositories2.domain.mounters import unversioned_mounter


def test_unversioned_mounter_pass(tmp_path: Path) -> None:
    """It mounts the filesystem."""
    mount = unversioned_mounter(DiskFilesystem)
    filesystem = mount(tmp_path, None)
    assert isinstance(filesystem, DiskFilesystem)


def test_unversioned_mounter_fail(tmp_path: Path) -> None:
    """It raises an exception."""
    mount = unversioned_mounter(DiskFilesystem)
    with pytest.raises(Exception):
        mount(tmp_path, "v1.0.0")
