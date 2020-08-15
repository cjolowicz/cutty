"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Optional

import poyo.exceptions

from . import exceptions
from . import locations


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
        """Expand abbreviations in a template location.

        Args:
            template: The project template location.

        Returns:
            The expanded project template.
        """
        if template in self.abbreviations:
            return self.abbreviations[template]

        prefix, _, rest = template.partition(":")
        if prefix in self.abbreviations:
            return self.abbreviations[prefix].format(rest)

        return template


@dataclass
class Config:
    """Configuration."""

    default_context: Mapping[str, Any] = field(default_factory=dict)
    abbreviations: Abbreviations = field(default_factory=Abbreviations)

    @classmethod
    def load(
        cls, path: Optional[Path] = None, *, ignore_config: bool = False
    ) -> Config:
        """Return the user configuration."""
        if ignore_config or (path is None and not locations.config.exists()):
            return cls()

        if path is None:
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

        if "default_context" in data:
            config.default_context = data["default_context"]

        if "abbreviations" in data:
            config.abbreviations.update(data["abbreviations"])

        return config
