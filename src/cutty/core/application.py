"""Application."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import locations
from .cache import Cache
from .compat import contextmanager
from .config import Config
from .engine import Engine
from .project import Project
from .template import Template


@dataclass
class Application:
    """Application."""

    config: Config
    cache: Cache

    @classmethod
    def create(
        cls, *, config_file: Optional[Path] = None, cache_dir: Optional[Path] = None
    ) -> Application:
        """Create an application."""
        if cache_dir is None:
            cache_dir = locations.cache

        if config_file is None:
            config_file = locations.config

        config = Config.load(config_file)
        cache = Cache(cache_dir)

        return cls(config=config, cache=cache)

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
    def load_template_for_project(
        self,
        project: Project,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None
    ) -> Iterator[Template]:
        """Load a template."""
        with self.load_template(
            project.variables.location, directory=directory, revision=revision
        ) as template:
            variables = template.variables.override(project.variables)
            yield replace(template, variables=variables)

    def generate_project(
        self,
        template: Template,
        *,
        output_dir: Optional[Path] = None,
        interactive: bool = False,
        overwrite: bool = False
    ) -> Project:
        """Generate a project from a template."""
        if output_dir is None:
            output_dir = Path.cwd()

        engine = Engine(template, interactive=interactive, overwrite=overwrite)
        path = engine.generate(output_dir)

        return Project.create(path, name=template.name, version=template.version)

    def update_project(
        self,
        project: Project,
        *,
        interactive: bool = False,
        directory: Optional[Path] = None,
        revision: Optional[str] = None
    ):
        """Update a project with changes from its template."""
        with self.load_template_for_project(
            project, directory=directory, revision=revision
        ) as template:
            with project.update(
                name=template.name, version=template.version
            ) as worktree:
                self.generate_project(
                    template,
                    output_dir=worktree.parent,
                    interactive=interactive,
                    overwrite=True,
                )
