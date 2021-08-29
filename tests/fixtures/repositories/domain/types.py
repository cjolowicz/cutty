"""Types."""
import pathlib
from typing import Optional

from yarl import URL


FetcherCalls = list[tuple[URL, pathlib.Path, Optional[str]]]
