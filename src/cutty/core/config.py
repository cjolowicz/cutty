"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Mapping
from typing import Optional

import poyo.exceptions

from . import exceptions
from . import locations
from .utils import with_context


class Abbreviations:
    """Abbreviations for template locations."""

    def __init__(self) -> None:
        """Initialize."""
        self.abbreviations = {
            "gh": "https://github.com/{}.git",
            "gl": "https://gitlab.com/{}.git",
            "bb": "https://bitbucket.org/{}",
        }

    def update(self, abbreviations: Mapping[str, str]) -> None:
        """Update the registered abbreviations."""
        self.abbreviations.update(abbreviations)

    def expand(self, template: str) -> str:
        """Expand abbreviations in a template location."""
        if template in self.abbreviations:
            return self.abbreviations[template]

        prefix, _, rest = template.partition(":")
        abbreviation = self.abbreviations.get(prefix)
        if abbreviation is not None:
            with exceptions.InvalidAbbreviation(prefix, abbreviation):
                return abbreviation.format(rest)

        return template


@dataclass
class Config:
    """Configuration."""

    abbreviations: Abbreviations = field(default_factory=Abbreviations)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> Config:
        """Return the user configuration."""
        if path is None:
            if not locations.config.exists():
                return cls()

            path = locations.config

        return cls._load(path)

    @with_context(
        lambda path: (
            exceptions.ConfigurationDoesNotExist(path).when(FileNotFoundError),
            exceptions.InvalidConfiguration(path).when(poyo.exceptions.PoyoException),
            exceptions.ConfigurationError(path),
        )
    )
    @classmethod
    def _load(cls, path: Path) -> Config:
        text = path.read_text()
        data = poyo.parse_string(text)
        config = cls()

        if "abbreviations" in data:
            config.abbreviations.update(data["abbreviations"])

        return config
