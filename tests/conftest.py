"""Common fixtures."""
import pathlib
import platform

import pytest


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
    monkeypatch.setattr("platformdirs.user_cache_dir", lambda *args, **kwargs: path)


@pytest.fixture(autouse=platform.system() == "Windows")
def set_storage_digest_size(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid errors due to excessively long paths on Windows."""
    monkeypatch.setattr("cutty.repositories.adapters.storage.DIGEST_SIZE", 3)


@pytest.fixture(scope="session")
def session_tmp_path(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Return a temporary directory path object for the entire pytest session.

    The directory is created as a sub directory of the base temporary
    directory.

    By default, a new base temporary directory is created each test session,
    and old bases are removed after 3 sessions, to aid in debugging. If
    ``--basetemp`` is used then it is cleared each session. See :ref:`base
    temporary directory`.

    The returned object is a :class:`pathlib.Path` object.
    """
    return tmp_path_factory.mktemp("session_tmp_path", numbered=True)
