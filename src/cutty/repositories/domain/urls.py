"""Utilities for URLs and paths."""
import os.path
import pathlib
import platform

from yarl import URL


def aspath(url: URL) -> pathlib.Path:
    """Convert URL to filesystem path."""
    if any(
        (
            url.scheme and url.scheme != "file",
            url.host and platform.system() != "Windows",
            url.user,
            url.password,
            url.port,
            url.query_string,
            url.fragment,
        )
    ):
        raise ValueError(f"not a path: {url}")

    if platform.system() == "Windows":
        if url.host:
            return pathlib.Path(f"//{url.host}{url.path}")

        path = pathlib.Path(url.path[1:])
        if path.drive:
            return path

    return pathlib.Path(url.path)


def realpath(path: pathlib.Path) -> pathlib.Path:
    """Return the canonical path of the specified filename."""
    return pathlib.Path(os.path.realpath(path))


def asurl(path: pathlib.Path) -> URL:
    """Convert filesystem path to URL."""
    # Get an absolute path but avoid Path.resolve.
    # https://bugs.python.org/issue38671
    path = realpath(path)

    return URL(path.as_uri())


def parseurl(location: str) -> URL:
    """Construct a URL from a string."""
    path = pathlib.Path(location)
    if not path.exists():
        url = URL(location)
        if url.scheme:
            return url

    return asurl(path)
