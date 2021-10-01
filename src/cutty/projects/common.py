"""Common functionality for projects."""
from collections.abc import Callable
from pathlib import Path


GenerateProject = Callable[[Path], None]
