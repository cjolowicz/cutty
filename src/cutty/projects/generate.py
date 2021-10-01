"""Generating projects from templates."""
import itertools
import pathlib
from collections.abc import Sequence

from lazysequence import lazysequence

from cutty.errors import CuttyError
from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
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


class ProjectGenerator:
    """Project generator."""

    def __init__(
        self,
        template: Template,
        *,
        extrabindings: Sequence[Binding],
        no_input: bool,
        overwrite_if_exists: bool,
        skip_if_file_exists: bool,
    ) -> None:
        """Initialize."""
        self.template = template
        self.extrabindings = extrabindings
        self.no_input = no_input
        self.overwrite_if_exists = overwrite_if_exists
        self.skip_if_file_exists = skip_if_file_exists

    def generate(
        self,
        outputdir: pathlib.Path,
        *,
        outputdirisproject: bool,
        createconfigfile: bool,
    ) -> pathlib.Path:
        """Generate a project from a project template."""
        config = loadcookiecutterconfig(
            self.template.metadata.location, self.template.root
        )
        render = createcookiecutterrenderer(self.template.root, config)
        bindings = bindcookiecuttervariables(
            config.variables,
            render,
            interactive=not self.no_input,
            bindings=self.extrabindings,
        )

        projectconfig = ProjectConfig(
            self.template.metadata.location,
            bindings,
            directory=self.template.metadata.directory,
        )
        projectfiles = lazysequence(
            renderfiles(
                findcookiecutterpaths(self.template.root, config), render, bindings
            )
        )
        if not projectfiles:
            raise EmptyTemplateError()

        projectname = projectfiles[0].path.parts[0]
        projectfiles2 = projectfiles.release()
        if createconfigfile:
            projectconfigfile = createprojectconfigfile(
                PurePath(projectname), projectconfig
            )
            projectfiles2 = itertools.chain(projectfiles2, [projectconfigfile])

        hookfiles = lazysequence(
            renderfiles(findcookiecutterhooks(self.template.root), render, bindings)
        )

        projectdir = outputdir if outputdirisproject else outputdir / projectname
        storage = createcookiecutterstorage(
            outputdir,
            projectdir,
            self.overwrite_if_exists,
            self.skip_if_file_exists,
            hookfiles,
        )

        with storage:
            for projectfile in projectfiles2:
                if outputdirisproject:
                    path = PurePath(*projectfile.path.parts[1:])
                    projectfile = projectfile.withpath(path)

                storage.add(projectfile)

        return projectdir


def generate(
    template: Template,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    outputdirisproject: bool,
    createconfigfile: bool,
) -> pathlib.Path:
    """Generate a project from a project template."""
    return ProjectGenerator(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    ).generate(
        outputdir,
        outputdirisproject=outputdirisproject,
        createconfigfile=createconfigfile,
    )
