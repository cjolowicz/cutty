"""Configuration."""
from dataclasses import dataclass
from typing import Any

from cutty.templates.domain.variables import Variable


@dataclass
class Config:
    """Template configuration."""

    settings: dict[str, Any]
    variables: tuple[Variable, ...]
