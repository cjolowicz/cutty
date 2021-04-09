"""Utilities for URLs and paths."""
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

    return pathlib.Path(f"//{url.host}{url.path}" if url.host else url.path)


def asurl(path: pathlib.Path) -> URL:
    """Convert filesystem path to URL."""
    return URL(path.resolve().as_uri())


def parseurl(location: str) -> URL:
    """Construct a URL from a string."""
    path = pathlib.Path(location)
    return asurl(path) if path.exists() else URL(location)
