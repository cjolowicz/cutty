"""Utilities for URLs and paths."""
import os.path
import pathlib
import platform
from typing import Union

from yarl import URL


Location = Union[pathlib.Path, URL]


def aspurewindowspath(url: URL) -> pathlib.PureWindowsPath:
    """Convert URL to Windows filesystem path."""
    if any(
        (
            url.scheme and url.scheme != "file",
            url.user,
            url.password,
            url.port,
            url.query_string,
            url.fragment,
        )
    ):
        raise ValueError(f"not a path: {url}")

    if url.host:
        return pathlib.PureWindowsPath(f"//{url.host}{url.path}")

    path = pathlib.PureWindowsPath(url.path[1:])
    if path.drive:
        return path

    return pathlib.PureWindowsPath(url.path)


def aspureposixpath(url: URL) -> pathlib.PurePosixPath:
    """Convert URL to POSIX filesystem path."""
    if any(
        (
            url.scheme and url.scheme != "file",
            url.host,
            url.user,
            url.password,
            url.port,
            url.query_string,
            url.fragment,
        )
    ):
        raise ValueError(f"not a path: {url}")

    return pathlib.PurePosixPath(url.path)


def aspath(url: URL) -> pathlib.Path:
    """Convert URL to filesystem path."""
    return pathlib.Path(
        aspurewindowspath(url)
        if platform.system() == "Windows"
        else aspureposixpath(url)
    )


def realpath(path: pathlib.Path) -> pathlib.Path:
    """Return the canonical path of the specified filename."""
    return pathlib.Path(os.path.realpath(path))


def asurl(path: pathlib.Path) -> URL:
    """Convert filesystem path to URL."""
    # Get an absolute path but avoid Path.resolve.
    # https://bugs.python.org/issue38671
    path = realpath(path)

    return URL(path.as_uri())


def parselocation(location: str) -> Location:
    """Construct a path or URL from a string."""
    path = pathlib.Path(location)

    try:
        exists = path.exists()
    except OSError:  # pragma: no cover
        exists = False  # illegal filename on Windows

    if not exists:
        url = URL(location)

        # A location without a scheme can be one of three things: a vanilla
        # path, a UNC-style Windows path, or a network-path reference (RFC 3986)
        # a.k.a. protocol-relative URL. The first two are paths, and the third
        # makes no sense without a base URI. So we treat all as paths.

        if url.scheme:
            return url

    return path
