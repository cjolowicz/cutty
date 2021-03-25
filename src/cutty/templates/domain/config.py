"""Configuration."""
from dataclasses import dataclass

from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.variables import Variable


@dataclass
class Config:
    """Template configuration."""

    settings: tuple[Binding, ...]
    variables: tuple[Variable, ...]
