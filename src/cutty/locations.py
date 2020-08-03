"""Locations."""
from pathlib import Path

import appdirs


name = "cutty"
cache = Path(appdirs.user_cache_dir(appname=name, appauthor=name))
