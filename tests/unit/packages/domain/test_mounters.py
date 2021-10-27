"""Unit tests for cutty.packages.domain.mounters."""
from pathlib import Path

import pytest

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.packages.domain.mounters import unversioned_mounter2


def test_unversioned_mounter_pass(tmp_path: Path) -> None:
    """It mounts the filesystem."""
    mount = unversioned_mounter2(DiskFilesystem)
    with mount(tmp_path, None) as filesystem:
        assert isinstance(filesystem, DiskFilesystem)


def test_unversioned_mounter_fail(tmp_path: Path) -> None:
    """It raises an exception."""
    mount = unversioned_mounter2(DiskFilesystem)
    with pytest.raises(Exception):
        with mount(tmp_path, "v1.0.0"):
            pass
