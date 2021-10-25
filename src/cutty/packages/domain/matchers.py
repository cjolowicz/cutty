"""Matching URLs and paths."""
import pathlib
from collections.abc import Callable

from yarl import URL


Matcher = Callable[[URL], bool]
PathMatcher = Callable[[pathlib.Path], bool]


def scheme(*args: str) -> Matcher:
    """Return a matcher for the given URL schemes."""
    schemes = set(args)

    def _match(url: URL) -> bool:
        return url.scheme in schemes or ("file" in schemes and not url.scheme)

    return _match
