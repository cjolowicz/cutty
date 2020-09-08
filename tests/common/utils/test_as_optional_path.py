"""Test cases for cutty.common.utils.as_optional_path."""
from pathlib import Path

from cutty.common.utils import as_optional_path


def test_none() -> None:
    """It returns None when passed None."""
    result = as_optional_path(None)
    assert result is None


def test_string() -> None:
    """It returns an instance of Path when passed a string."""
    result = as_optional_path("some/path")
    assert isinstance(result, Path)
