"""Configuration."""
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Mapping
from typing import Optional

import cookiecutter.config


@dataclass
class Config:
    """Configuration."""

    default_context: Mapping[str, Any]
    abbreviations: Mapping[str, str]


DEFAULT_PATH = Path("~/.cookiecutterrc").expanduser()
DEFAULT_CONFIG = Config(
    default_context={},
    abbreviations={
        "gh": "https://github.com/{}.git",
        "gl": "https://gitlab.com/{}.git",
        "bb": "https://bitbucket.org/{}",
    },
)


def get_user_config(
    config_file: Optional[Path] = None, default_config: bool = False
) -> Config:
    """Return the user configuration."""
    if default_config or (config_file is None and not DEFAULT_PATH.exists()):
        return DEFAULT_CONFIG

    path = config_file if config_file is not None else DEFAULT_PATH
    config = cookiecutter.config.get_config(str(path))
    return Config(
        default_context=config["default_context"],
        abbreviations=config["abbreviations"],
    )
