"""Functional tests for `cutty link`."""
from tests.functional.conftest import RunCutty


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("link", "--help")
