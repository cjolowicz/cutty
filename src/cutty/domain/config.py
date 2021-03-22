"""Configuration."""
from dataclasses import dataclass

from cutty.domain.bindings import Binding
from cutty.domain.variables import Variable


@dataclass
class TemplateConfig:
    """Template configuration."""

    settings: tuple[Binding, ...]
    variables: tuple[Variable, ...]
