"""Functional tests for the cutty CLI."""
from importlib.metadata import version

from tests.functional.conftest import RunCutty


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("--help")


def test_version(runcutty: RunCutty) -> None:
    """It displays the version."""
    assert version("cutty") in runcutty("--version")
