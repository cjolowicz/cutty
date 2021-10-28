"""Functional tests for `cutty import`."""
from tests.functional.conftest import RunCutty


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("import", "--help")
