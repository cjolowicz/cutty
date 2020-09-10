"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Iterator
from typing import Mapping
from typing import Optional

import poyo.exceptions

from . import exceptions
from . import locations
from .compat import contextmanager


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


@contextmanager
def handle_errors(path: Path) -> Iterator[None]:
    """Handle errors."""
    try:
        yield
    except FileNotFoundError:
        raise exceptions.ConfigurationDoesNotExist(
            f"Cannot load configuration: {path}: File does not exist."
        )
    except poyo.exceptions.PoyoException as error:
        raise exceptions.InvalidConfiguration(
            f"Configuration file {path} is invalid: {error}"
        )
    except Exception as error:
        raise exceptions.InvalidConfiguration(
            f"Configuration file {path} cannot be loaded: {error}"
        )


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

        with handle_errors(path):
            text = path.read_text()
            data = poyo.parse_string(text)

        config = cls()

        if "abbreviations" in data:
            config.abbreviations.update(data["abbreviations"])

        return config
