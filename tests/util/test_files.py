"""Tests for file utilities."""
from pathlib import Path

import pytest

from tests.util.files import template_files


def test_template_files(tmp_path: Path) -> None:
    """It raises StopIteration if there is no template repository."""
    with pytest.raises(StopIteration):
        template_files(tmp_path)
