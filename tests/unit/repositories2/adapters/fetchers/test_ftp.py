"""Unit tests for cutty.repositories2.adapters.fetchers.ftp."""
import os
from collections.abc import Iterator
from pathlib import Path
from threading import Event
from threading import Thread

import pytest
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from yarl import URL

from cutty.repositories2.adapters.fetchers.ftp import ftpfetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.stores import Store


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    path = tmp_path / "repository.txt"
    path.write_text("Lorem")
    return path


@pytest.fixture
def server(repository: Path) -> Iterator[URL]:
    """Fixture for an FTP server exposing the repository."""
    # Bind to 127.0.0.1 not localhost, because IPv6 is not supported.
    # (urllib.request.FTPHandler uses socket.gethostbyname.)
    address = ("127.0.0.1", 0)
    timeout = 0.001 if os.environ.get("CI") else 0.000001

    handler = FTPHandler
    handler.authorizer = DummyAuthorizer()
    handler.authorizer.add_anonymous(str(repository.parent))

    with FTPServer(address, handler) as server:
        done = Event()
        shutdown = False

        def run() -> None:
            try:
                while not shutdown:
                    server.serve_forever(timeout=timeout, blocking=False)
            finally:
                done.set()

        thread = Thread(target=run, daemon=True)
        thread.start()

        host, port = server.address
        path = f"/{repository.name}"

        yield URL.build(scheme="ftp", host=host, port=port, path=path)

        shutdown = True
        done.wait()

    thread.join()


defaults = dict(revision=None, mode=FetchMode.ALWAYS)


def test_ftpfetcher_happy(server: URL, store: Store, repository: Path) -> None:
    """It downloads the file."""
    path = ftpfetcher(server, store, **defaults)
    assert path.read_text() == repository.read_text()


def test_ftpfetcher_not_matched(store: Store) -> None:
    """It returns None if the URL does not use the ftp scheme."""
    url = URL("file:///")
    path = ftpfetcher(url, store, **defaults)
    assert path is None


def test_ftpfetcher_not_found(server: URL, store: Store) -> None:
    """It raises an exception if the server responds with an error."""
    with pytest.raises(Exception):
        ftpfetcher(server.with_name("bogus"), store, **defaults)


def test_ftpfetcher_update(server: URL, store: Store, repository: Path) -> None:
    """It updates a file from a previous fetch."""
    ftpfetcher(server, store, **defaults)
    repository.write_text("ipsum")
    path = ftpfetcher(server, store, **defaults)

    assert path.read_text() == repository.read_text()
