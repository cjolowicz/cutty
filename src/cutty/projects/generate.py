"""Generating projects from templates."""
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
from cutty.templates.domain.renderfiles import renderfiles


class EmptyTemplateError(CuttyError):
    """The template contains no project files."""


@dataclass
class Project:
    """Project generated from a template."""

    name: str
    files: Iterable[File]
    hooks: Iterable[File]


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
    config = loadcookiecutterconfig(template.metadata.location, template.root)
    render = createcookiecutterrenderer(template.root, config)
    bindings = bindcookiecuttervariables(
        config.variables,
        render,
        interactive=not no_input,
        bindings=extrabindings,
    )

    projectconfig = ProjectConfig(
        template.metadata.location, bindings, directory=template.metadata.directory
    )
    projectfileseq = lazysequence(
        renderfiles(findcookiecutterpaths(template.root, config), render, bindings)
    )
    if not projectfileseq:
        raise EmptyTemplateError()

    projectname = projectfileseq[0].path.parts[0]
    projectfiles = projectfileseq.release()
    hookfiles = renderfiles(findcookiecutterhooks(template.root), render, bindings)
    project = Project(projectname, projectfiles, hookfiles)

    if createconfigfile:
        projectconfigfile = createprojectconfigfile(
            PurePath(projectname), projectconfig
        )
        project.files = itertools.chain(project.files, [projectconfigfile])

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
