"""Test fixtures."""
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from cutty import cache
from cutty import git


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Initialize repository in a temporary directory."""
    path = tmp_path / "repository"
    path.mkdir()
    return git.Repository.init(path)


@pytest.fixture
def user_cache_dir(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Replace the application cache directory by a temporary directory."""
    path = tmp_path / ".cache" / cache.appname
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("appdirs.user_cache_dir", lambda *args, **kwargs: path)
    return path
