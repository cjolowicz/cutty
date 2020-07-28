"""General-purpose utilities."""
from pathlib import Path
from typing import Optional
from typing import TypeVar

T = TypeVar("T")


def as_optional_str(argument: Optional[T]) -> Optional[str]:
    """Convert the argument to a string if it is not None."""
    return str(argument) if argument is not None else None


def as_optional_path(argument: Optional[str]) -> Optional[Path]:
    """Convert the argument to a Path if it is not None."""
    return Path(argument) if argument is not None else None
