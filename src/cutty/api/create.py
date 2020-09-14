"""Create a project."""
from pathlib import Path
from typing import Optional

from ..core.cache import cache
from ..core.config import Config
from ..core.engine import Engine


def create(
    location: str,
    *,
    interactive: bool = True,
    revision: Optional[str] = None,
    directory: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Create a project from a Cookiecutter template."""
    config = Config.load(config_file)
    location = config.abbreviations.expand(location)

    with cache.load(location, directory=directory, revision=revision) as template:
        engine = Engine(template, interactive=interactive)
        engine.generate(output_dir or Path())
