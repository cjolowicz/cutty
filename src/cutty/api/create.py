"""Create a project."""
from pathlib import Path
from typing import Optional

from ..core.cache import Cache
from ..core.config import Config
from .engine import Engine
from .template import Template


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

    with Cache.load(location, directory=directory, revision=revision) as cache:
        template = Template.load(cache.repository, location=location)
        engine = Engine(template, interactive=interactive)
        engine.generate(output_dir or Path())
