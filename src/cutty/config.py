"""Configuration."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Optional

import cookiecutter.config

from .utils import as_optional_str


@dataclass
class Config:
    """Configuration."""

    default_context: Mapping[str, Any]
    abbreviations: Mapping[str, str]


def get_user_config(
    config_file: Optional[Path] = None, default_config: bool = False
) -> Config:
    """Return the user configuration."""
    config = cookiecutter.config.get_user_config(
        config_file=as_optional_str(config_file), default_config=default_config
    )
    return Config(
        default_context=config["default_context"], abbreviations=config["abbreviations"]
    )
