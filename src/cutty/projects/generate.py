"""Generating projects from templates."""
from __future__ import annotations

import dataclasses
import itertools
import pathlib
from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass

from lazysequence import lazysequence

from cutty.errors import CuttyError
from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.domain.files import File
from cutty.filesystems.domain.purepath import PurePath
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


class EmptyTemplateError(CuttyError):
    """The template contains no project files."""


@dataclass(frozen=True)
class Project:
    """A generated project."""

    name: str
    files: Iterable[File]
    hooks: Iterable[File]

    @classmethod
    def create(cls, files: Iterable[File], hooks: Iterable[File]) -> Project:
        """Create a project."""
        fileseq = lazysequence(files)

        try:
            first = fileseq[0]
        except IndexError:
            raise EmptyTemplateError()

        files = fileseq.release()
        name = first.path.parts[0]
        return Project(name, files, hooks)

    def add(self, file: File) -> Project:
        """Add a project file."""
        return dataclasses.replace(self, files=itertools.chain(self.files, [file]))


@dataclass(frozen=True)
class ProjectGenerator:
    """A project generator."""

    config: Config
    render: Renderer

    @classmethod
    def create(cls, template: Template) -> ProjectGenerator:
        """Create a project generator."""
        config = loadcookiecutterconfig(template.metadata.location, template.root)
        render = createcookiecutterrenderer(template.root, config)
        return cls(config, render)


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
        generator.config.variables,
        generator.render,
        interactive=not no_input,
        bindings=extrabindings,
    )

    projectfiles = renderfiles(
        findcookiecutterpaths(template.root, generator.config),
        generator.render,
        bindings,
    )
    hookfiles = renderfiles(
        findcookiecutterhooks(template.root), generator.render, bindings
    )
    project = Project.create(projectfiles, hookfiles)

    if createconfigfile:
        projectconfig = ProjectConfig(
            template.metadata.location, bindings, directory=template.metadata.directory
        )
        projectconfigfile = createprojectconfigfile(
            PurePath(project.name), projectconfig
        )
        project = project.add(projectconfigfile)

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
