"""Common fixtures."""
import pathlib
import platform

import pytest


@pytest.fixture(autouse=platform.system() == "Windows")
def set_hg_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide author information to ``hg commit``."""
    monkeypatch.setenv("HGUSER", "you@example.com")


@pytest.fixture(autouse=True)
def set_git_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide author information to git."""
    monkeypatch.setenv("GIT_AUTHOR_NAME", "You")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "you@example.com")


@pytest.fixture(autouse=True)
def set_user_cache_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """Replace the user cache directory by a temporary directory."""
    path = tmp_path / "user_cache_dir"
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("appdirs.user_cache_dir", lambda *args, **kwargs: path)


@pytest.fixture(autouse=platform.system() == "Windows")
def set_storage_digest_size(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid errors due to excessively long paths on Windows."""
    monkeypatch.setattr("cutty.repositories.adapters.storage.DIGEST_SIZE", 3)
