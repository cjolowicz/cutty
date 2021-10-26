"""Types."""
import pathlib

from yarl import URL


FetcherCalls = list[tuple[URL, pathlib.Path]]
