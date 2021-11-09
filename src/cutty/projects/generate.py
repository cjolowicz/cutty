"""Project generator."""
from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.config import createprojectconfigfile
from cutty.projects.config import ProjectConfig
from cutty.projects.cookiecutter import findcookiecutterhooks
from cutty.projects.cookiecutter import findcookiecutterpaths
from cutty.projects.cookiecutter import loadcookiecutterconfig
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.rendering.adapters.cookiecutter import CookiecutterConfig
from cutty.rendering.adapters.cookiecutter import createcookiecutterrenderer
from cutty.rendering.domain.render import Renderer
from cutty.rendering.domain.renderbind import renderbind
from cutty.rendering.domain.renderfiles import renderfiles
from cutty.variables.adapters.prompts import createprompt
from cutty.variables.domain.binders import binddefault
from cutty.variables.domain.binders import Binder
from cutty.variables.domain.binders import override
from cutty.variables.domain.bindings import Binding


@dataclass(frozen=True)
class ProjectGenerator:
    """A project generator."""

    _template: Template.Metadata
    _config: CookiecutterConfig
    _renderer: Renderer
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

    def bind(
        self, *, interactive: bool = True, bindings: Sequence[Binding] = ()
    ) -> Sequence[Binding]:
        """Bind the variables."""
        binder: Binder = createprompt() if interactive else binddefault
        binder = override(binder, bindings)
        return renderbind(self._renderer, binder, self._config.variables)

    def generate(self, bindings: Sequence[Binding]) -> Project:
        """Generate a project using the given bindings."""
        files = renderfiles(self._paths, self._renderer, bindings)
        hooks = renderfiles(self._hooks, self._renderer, bindings)
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


def generate(
    template: Template,
    bindings: Sequence[Binding] = (),
    /,
    *,
    interactive: bool,
    createconfigfile: bool = True,
) -> Project:
    """Generate a project from a project template."""
    generator = ProjectGenerator.create(template)
    bindings = generator.bind(interactive=interactive, bindings=bindings)
    project = generator.generate(bindings)

    if createconfigfile:
        project = generator.addconfig(project, bindings)

    return project
