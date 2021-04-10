"""Unit tests for cutty.repositories2.adapters.fetchers.http."""
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
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()

        host, port = server.server_address
        path = f"/{repository.name}"
        yield URL.build(scheme="http", host=host, port=port, path=path)

        server.shutdown()
        thread.join()


defaults = dict(revision=None, mode=FetchMode.ALWAYS)


def test_httpfetcher_happy(server: URL, store: Store, repository: Path):
    """It downloads the file."""
    path = httpfetcher(server, store, **defaults)
    assert path.read_text() == repository.read_text()


def test_httpfetcher_not_matched(store: Store):
    """It returns None if the URL does not use the http scheme."""
    url = URL("file:///")
    path = httpfetcher(url, store, **defaults)
    assert path is None


def test_httpfetcher_not_found(server: URL, store: Store):
    """It raises an exception if the server responds with an error."""
    with pytest.raises(Exception):
        httpfetcher(server.with_name("bogus"), store, **defaults)


def test_httpfetcher_update(server: URL, store: Store, repository: Path):
    """It updates a file from a previous fetch."""
    httpfetcher(server, store, **defaults)
    repository.write_text("ipsum")
    path = httpfetcher(server, store, **defaults)

    assert path.read_text() == repository.read_text()
