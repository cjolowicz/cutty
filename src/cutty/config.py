"""Configuration."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Optional

import cookiecutter.exceptions
import poyo.exceptions


DEFAULT_PATH = Path("~/.cookiecutterrc").expanduser()
DEFAULT_ABBREVIATIONS = {
    "gh": "https://github.com/{}.git",
    "gl": "https://gitlab.com/{}.git",
    "bb": "https://bitbucket.org/{}",
}


@dataclass
class Config:
    """Configuration."""

    default_context: Mapping[str, Any] = field(default_factory=dict)
    abbreviations: Mapping[str, str] = field(
        default_factory=lambda: dict(DEFAULT_ABBREVIATIONS)
    )

    @classmethod
    def load(cls, path: Optional[Path] = None, default_config: bool = False) -> Config:
        """Return the user configuration."""
        if default_config or (path is None and not DEFAULT_PATH.exists()):
            return cls()

        if path is None:
            path = DEFAULT_PATH
        elif not path.exists():
            raise cookiecutter.exceptions.ConfigDoesNotExistException(
                f"Config file {path} does not exist."
            )

        text = path.read_text()

        try:
            data = poyo.parse_string(text)
        except poyo.exceptions.PoyoException as error:
            raise cookiecutter.exceptions.InvalidConfiguration(
                f"Unable to parse YAML file {path}. Error: {error}"
            )

        config = cls()

        if "default_context" in data:
            config.default_context = data["default_context"]

        if "abbreviations" in data:
            config.abbreviations = {**config.abbreviations, **data["abbreviations"]}

        return config
