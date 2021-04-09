"""Utilities for URLs and paths."""
import pathlib

from yarl import URL


def asurl(path: pathlib.Path) -> URL:
    """Convert filesystem path to URL."""
    return URL(path.resolve().as_uri())


def parseurl(location: str) -> URL:
    """Construct a URL from a string."""
    path = pathlib.Path(location)
    return asurl(path) if path.exists() else URL(location)
