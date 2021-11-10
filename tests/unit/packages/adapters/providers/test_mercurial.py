"""Unit tests for cutty.packages.adapters.providers.mercurial."""
import pathlib
import string
from typing import Optional

import pytest
from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.adapters.fetchers.mercurial import Hg
from cutty.packages.adapters.providers.mercurial import hgproviderfactory
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.stores import Store

pytest_plugins = ["tests.fixtures.packages.adapters.mercurial"]


@pytest.fixture(scope="session")
def hgrepository(hg: Hg, session_tmp_path: pathlib.Path) -> pathlib.Path:
    """Session fixture for a Mercurial repository."""
    path = session_tmp_path / "repository"
    path.mkdir()

    hg("init", cwd=path)

    marker = path / "marker"
    marker.write_text("Lorem")

    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    hg("tag", "--message=Release v1.0", "v1.0", cwd=path)

    marker.write_text("Ipsum")

    hg("add", "marker", cwd=path)
    hg("commit", "--message=Update marker", cwd=path)

    return path


@pytest.fixture
def hgprovider(store: Store) -> Provider:
    """Fixture for a Mercurial provider."""
    return hgproviderfactory(store)


@pytest.mark.parametrize(
    ("revision", "expected"),
    [
        ("v1.0", "Lorem"),
        (None, "Ipsum"),
    ],
)
def test_happy(
    hgprovider: Provider,
    hgrepository: pathlib.Path,
    revision: Optional[str],
    expected: str,
) -> None:
    """It fetches a hg repository into storage."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get(revision) as package:
        text = (package.tree / "marker").read_text()
        assert expected == text


def is_mercurial_shorthash(revision: str) -> bool:
    """Return True if the text is a short changeset identification hash."""
    return len(revision) == 12 and all(c in string.hexdigits for c in revision)


def is_mercurial_hash(revision: str) -> bool:
    """Return True if the text is a full changeset identification hash."""
    return len(revision) == 40 and all(c in string.hexdigits for c in revision)


def test_revision_commit(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It retrieves the short hash as the package revision."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get() as package:
        assert package.commit is not None and is_mercurial_shorthash(
            package.commit.revision
        )


def test_revision_tag(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It retrieves the tag name as the package revision."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get("tip~2") as package:
        assert package.commit is not None and package.commit.revision == "v1.0"


def test_revision_no_tags(hgprovider: Provider, hg: Hg, tmp_path: pathlib.Path) -> None:
    """It retrieves the short hash as the package revision when there are no tags."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)

    repository = hgprovider.provide(path)

    assert repository is not None

    with repository.get() as package:
        assert package.commit is not None and is_mercurial_shorthash(
            package.commit.revision
        )


def test_revision_multiple_tags(
    hgprovider: Provider, hg: Hg, tmp_path: pathlib.Path
) -> None:
    """It retrieves multiple tag names separated by colon as the package revision."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").touch()

    hg("init", cwd=path)
    hg("add", "marker", cwd=path)
    hg("commit", "--message=Initial", cwd=path)
    hg("tag", "--rev=0", "tag1", cwd=path)
    hg("tag", "--rev=0", "tag2", cwd=path)

    repository = hgprovider.provide(path)

    assert repository is not None

    with repository.get("tip~2") as package:
        assert package.commit is not None and package.commit.revision == "tag1:tag2"


def test_not_matching(hgprovider: Provider) -> None:
    """It returns None if the URL scheme is not recognized."""
    repository = hgprovider.provide(URL("mailto:you@example.com"))

    assert repository is None


def test_update(hgrepository: pathlib.Path, store: Store) -> None:
    """It updates the repository from a previous fetch."""
    hgprovider = hgproviderfactory(store)

    def fetchrevision(revision: Optional[str]) -> Optional[str]:
        repository = hgprovider.provide(hgrepository)

        assert repository is not None

        with repository.get(revision) as package:
            return package.commit.revision if package.commit is not None else None

    revision1 = fetchrevision("v1.0")
    revision2 = fetchrevision(None)

    assert revision1 != revision2


def test_revision_not_found(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It raises an exception."""
    with pytest.raises(CuttyError):
        if repository := hgprovider.provide(hgrepository):
            with repository.get("invalid"):
                pass


def test_parent_revision_tip(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns the parent revision of the tip."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    revision = repository.getparentrevision(None)

    with repository.get(revision) as package:
        assert "Lorem" == (package.tree / "marker").read_text()


def test_parent_revision_root(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns None for the parent revision of the root."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    revision = repository.getparentrevision("v1.0")

    assert revision is None


def test_parent_revision_hash(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns the full revision identifier."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    # Skip over the changeset adding the tag.
    revision = repository.getparentrevision(repository.getparentrevision(None))

    assert revision is not None and is_mercurial_hash(revision)


def test_commit(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns the full revision identifier."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get(None) as package:
        assert package.commit is not None and is_mercurial_hash(package.commit.id)


def test_message(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns the commit message."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get(None) as package:
        assert package.commit is not None and package.commit.message


def test_author(hgprovider: Provider, hgrepository: pathlib.Path) -> None:
    """It returns the name and email of the commit author."""
    repository = hgprovider.provide(hgrepository)

    assert repository is not None

    with repository.get(None) as package:
        assert package.commit is not None
        assert "You" == package.commit.author.name
        assert "you@example.com" == package.commit.author.email
