"""Configuration."""
from pathlib import Path
from typing import cast
from typing import Optional

import cookiecutter.config

from ..types import StrMapping
from ..utils import as_optional_str


def get_user_config(
    config_file: Optional[Path] = None, default_config: bool = False
) -> StrMapping:
    """Return the user configuration."""
    config = cookiecutter.config.get_user_config(
        config_file=as_optional_str(config_file), default_config=default_config
    )
    return cast(StrMapping, config)
