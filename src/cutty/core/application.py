"""Application."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import locations
from .cache import Cache
from .compat import contextmanager
from .config import Config
from .engine import Engine
from .template import Template


@dataclass
class Application:
    """Application."""

    cache: Cache
    config: Config

    @classmethod
    def create(
        cls, *, config_file: Optional[Path] = None, cache_dir: Optional[Path] = None
    ) -> Application:
        """Create an application."""
        if cache_dir is None:
            cache_dir = locations.cache

        cache = Cache(cache_dir)
        config = Config.load(config_file)
        return cls(cache=cache, config=config)

    @contextmanager
    def load_template(
        self,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None
    ) -> Iterator[Template]:
        """Load a template."""
        location = self.config.abbreviations.expand(location)
        with self.cache.load(
            location, directory=directory, revision=revision
        ) as template:
            yield template

    @contextmanager
    def load_template_from_instance(
        self,
        instance: Path,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None
    ) -> Iterator[Template]:
        """Load a template."""
        location = Template.load_location(instance)
        location = self.config.abbreviations.expand(location)
        with self.cache.load(
            location, directory=directory, revision=revision
        ) as template:
            yield template

    def generate_project(
        self,
        template: Template,
        *,
        output_dir: Optional[Path] = None,
        interactive: bool = False,
        overwrite: bool = False
    ) -> None:
        """Generate a project from a template."""
        if output_dir is None:
            output_dir = Path.cwd()

        engine = Engine(template, interactive=interactive)
        engine.generate(output_dir, overwrite=overwrite)
