"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Mapping
from typing import Optional

import poyo.exceptions

from ..common import exceptions
from ..common import locations


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
        if prefix in self.abbreviations:
            return self.abbreviations[prefix].format(rest)

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
        elif not path.exists():
            raise exceptions.ConfigDoesNotExistException(
                f"Config file {path} does not exist."
            )

        text = path.read_text()

        try:
            data = poyo.parse_string(text)
        except poyo.exceptions.PoyoException as error:
            raise exceptions.InvalidConfiguration(
                f"Unable to parse YAML file {path}. Error: {error}"
            )

        config = cls()

        if "abbreviations" in data:
            config.abbreviations.update(data["abbreviations"])

        return config
