"""Tests for the versions module."""
from ..utils import commit
from cutty.core import git
from cutty.core import versions


def test_no_tags(repository: git.Repository) -> None:
    """It raises ValueError if there are no tags."""
    assert versions.find_latest_tag(repository) is None


def test_no_version_tags(repository: git.Repository) -> None:
    """It raises ValueError if the only tag does not identify a version."""
    commit(repository)
    repository.tag("bogus")
    assert versions.find_latest_tag(repository) is None


def test_single_version_tag(repository: git.Repository) -> None:
    """It returns the only tag if it identifies a version."""
    commit(repository)
    repository.tag("v1.0.0")
    tag = versions.find_latest_tag(repository)
    assert tag == versions.Tag.create("v1.0.0")


def test_multiple_version_tags(repository: git.Repository) -> None:
    """It returns the tag for the latest version."""
    repository.tag("v1.0.0", commit(repository))
    repository.tag("v1.0.1", commit(repository))
    tag = versions.find_latest_tag(repository)
    assert tag == versions.Tag.create("v1.0.1")
