"""Project generator."""
from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.config import createprojectconfigfile
from cutty.projects.config import ProjectConfig
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.templates.adapters.cookiecutter.config import findcookiecutterhooks
from cutty.templates.adapters.cookiecutter.config import findcookiecutterpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles
from cutty.variables.domain.bindings import Binding
from cutty.variables.domain.variables import Variable


@dataclass(frozen=True)
class ProjectGenerator:
    """A project generator."""

    _template: Template.Metadata
    _config: Config
    renderer: Renderer
    _paths: Iterable[Path]
    _hooks: Iterable[Path]

    @classmethod
    def create(cls, template: Template) -> ProjectGenerator:
        """Create a project generator."""
        config = loadcookiecutterconfig(template.metadata.location, template.root)
        renderer = createcookiecutterrenderer(template.root, config)
        paths = findcookiecutterpaths(template.root, config)
        hooks = findcookiecutterhooks(template.root)
        return cls(template.metadata, config, renderer, paths, hooks)

    @property
    def variables(self) -> Sequence[Variable]:
        """Return the template variables."""
        return self._config.variables

    def generate(self, bindings: Sequence[Binding]) -> Project:
        """Generate a project using the given bindings."""
        files = renderfiles(self._paths, self.renderer, bindings)
        hooks = renderfiles(self._hooks, self.renderer, bindings)
        return Project.create(self._template, files, hooks)

    def addconfig(self, project: Project, bindings: Sequence[Binding]) -> Project:
        """Add a configuration file to the project."""
        revision = (
            project.template.commit
            if project.template.commit is not None
            else project.template.revision
        )
        projectconfig = ProjectConfig(
            project.template.location,
            bindings,
            directory=project.template.directory,
            revision=revision,
        )
        projectconfigfile = createprojectconfigfile(
            PurePath(project.name), projectconfig
        )
        return project.add(projectconfigfile)
