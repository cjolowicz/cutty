"""Generating projects from templates."""
from __future__ import annotations

import pathlib
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filesystems.domain.path import Path
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.adapters.cookiecutter.config import findcookiecutterhooks
from cutty.templates.adapters.cookiecutter.config import findcookiecutterpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles
from cutty.templates.domain.variables import Variable


@dataclass(frozen=True)
class ProjectGenerator:
    """A project generator."""

    _template: Template
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
        return cls(template, config, renderer, paths, hooks)

    @property
    def variables(self) -> Sequence[Variable]:
        """Return the template variables."""
        return self._config.variables

    def generate(self, bindings: Sequence[Binding]) -> Project:
        """Generate a project using the given bindings."""
        files = renderfiles(self._paths, self.renderer, bindings)
        hooks = renderfiles(self._hooks, self.renderer, bindings)
        return Project.create(files, hooks)

    def addconfig(self, project: Project, bindings: Sequence[Binding]) -> Project:
        """Add a configuration file to the project."""
        projectconfig = ProjectConfig(
            self._template.metadata.location,
            bindings,
            directory=self._template.metadata.directory,
        )
        projectconfigfile = createprojectconfigfile(
            PurePath(project.name), projectconfig
        )
        return project.add(projectconfigfile)


def generate(
    template: Template,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    fileexists: FileExistsPolicy,
    outputdirisproject: bool,
    createconfigfile: bool,
) -> pathlib.Path:
    """Generate a project from a project template."""
    generator = ProjectGenerator.create(template)
    bindings = bindcookiecuttervariables(
        generator.variables,
        generator.renderer,
        interactive=not no_input,
        bindings=extrabindings,
    )

    project = generator.generate(bindings)

    if createconfigfile:
        project = generator.addconfig(project, bindings)

    return storeproject(
        project,
        outputdir,
        outputdirisproject,
        fileexists,
    )


def storeproject(
    project: Project,
    outputdir: pathlib.Path,
    outputdirisproject: bool,
    fileexists: FileExistsPolicy,
) -> pathlib.Path:
    """Store a project in the output directory."""
    projectdir = outputdir if outputdirisproject else outputdir / project.name
    storage = createcookiecutterstorage(
        outputdir, projectdir, fileexists, project.hooks
    )

    with storage:
        for projectfile in project.files:
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)

    return projectdir
