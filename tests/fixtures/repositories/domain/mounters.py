"""Fixtures for cutty.repositories.domain.mounters."""
import pytest

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.mounters import unversioned_mounter


@pytest.fixture
def defaultmount() -> Mounter:
    """Fixture with an unversioned disk filesystem mounter."""
    return unversioned_mounter(DiskFilesystem)
