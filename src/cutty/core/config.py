"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import poyo

from . import exceptions
from . import locations
from .abbreviations import Abbreviations


@dataclass
class Config:
    """Configuration."""

    abbreviations: Abbreviations = field(default_factory=Abbreviations)

    @classmethod
    def load(cls, path: Path) -> Config:
        """Return the user configuration."""
        if path == locations.config and not path.exists():
            return cls()

        with exceptions.ConfigurationFileError(
            path
        ), exceptions.ConfigurationDoesNotExist(path).when(FileNotFoundError):
            text = path.read_text()

        with exceptions.InvalidConfiguration(path):
            data = poyo.parse_string(text)

        config = cls()

        if "abbreviations" in data:
            config.abbreviations.update(data["abbreviations"])

        return config
