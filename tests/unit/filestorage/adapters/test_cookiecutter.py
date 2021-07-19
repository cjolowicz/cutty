"""Unit tests for cutty.filestorage.adapters.cookiecutter."""
from pathlib import Path

import pytest

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage


@pytest.mark.parametrize("createrepository", [True, False])
def test_createrepository(tmp_path: Path, createrepository: bool) -> None:
    """It creates a git repository."""
    storage = createcookiecutterstorage(
        tmp_path,
        tmp_path / "example",
        overwrite_if_exists=False,
        skip_if_file_exists=False,
        hookfiles=[],
        createrepository=createrepository,
    )

    with storage:
        pass

    assert createrepository is (tmp_path / "example" / ".git").is_dir()
