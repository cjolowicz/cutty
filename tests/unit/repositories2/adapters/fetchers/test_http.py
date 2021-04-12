"""Unit tests for cutty.repositories2.adapters.fetchers.http."""
import os
from collections.abc import Iterator
from functools import partial
from http.server import SimpleHTTPRequestHandler
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from yarl import URL

from cutty.repositories2.adapters.fetchers.http import httpfetcher
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
    """Fixture for an HTTP server exposing the repository."""
    address = ("localhost", 0)
    handler = partial(SimpleHTTPRequestHandler, directory=repository.parent)

    with ThreadingHTTPServer(address, handler) as server:
        target = partial(
            server.serve_forever,
            poll_interval=0.001 if os.environ.get("CI") else 0.000001,
        )
        thread = Thread(target=target, daemon=True)
        thread.start()

        host, port = server.server_address
        path = f"/{repository.name}"
        yield URL.build(scheme="http", host=host, port=port, path=path)

        server.shutdown()
        thread.join()


def test_httpfetcher_happy(server: URL, store: Store, repository: Path) -> None:
    """It downloads the file."""
    path = httpfetcher(server, store, None, FetchMode.ALWAYS)
    assert path.read_text() == repository.read_text()


def test_httpfetcher_not_matched(store: Store) -> None:
    """It returns None if the URL does not use the http scheme."""
    url = URL("file:///")
    path = httpfetcher(url, store, None, FetchMode.ALWAYS)
    assert path is None


def test_httpfetcher_not_found(server: URL, store: Store) -> None:
    """It raises an exception if the server responds with an error."""
    with pytest.raises(Exception):
        httpfetcher(server.with_name("bogus"), store, None, FetchMode.ALWAYS)


def test_httpfetcher_update(server: URL, store: Store, repository: Path) -> None:
    """It updates a file from a previous fetch."""
    httpfetcher(server, store, None, FetchMode.ALWAYS)
    repository.write_text("ipsum")
    path = httpfetcher(server, store, None, FetchMode.ALWAYS)

    assert path.read_text() == repository.read_text()
