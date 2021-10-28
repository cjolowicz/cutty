"""Functional tests for `cutty import`."""
from pathlib import Path

import pytest

from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.util.files import chdir


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("import", "--help")


@pytest.fixture
def project(runcutty: RunCutty, template: Path) -> Path:
    """Fixture for a generated project."""
    runcutty("create", "--non-interactive", str(template))

    return Path("example")


def test_noop(runcutty: RunCutty, project: Path) -> None:
    """It doesn't do anything if nothing changed."""
    head = Repository.open(project).head.commit

    with chdir(project):
        runcutty("import")

    assert head == Repository.open(project).head.commit
