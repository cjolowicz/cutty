"""Create a project from a Cookiecutter template."""
import itertools
import pathlib
from collections.abc import Sequence
from typing import Optional

import platformdirs
from lazysequence import lazysequence

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.repositories.domain.repository import Repository
from cutty.services.git import creategitrepository
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.adapters.cookiecutter.config import findcookiecutterhooks
from cutty.templates.adapters.cookiecutter.config import findcookiecutterpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.renderfiles import renderfiles


def loadtemplate(
    template: str, checkout: Optional[str], directory: Optional[pathlib.PurePosixPath]
) -> Repository:
    """Load a template repository."""
    cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
    repositoryprovider = getdefaultrepositoryprovider(cachedir)
    return repositoryprovider(
        template,
        revision=checkout,
        directory=(PurePath(*directory.parts) if directory is not None else None),
    )


class EmptyTemplateError(Exception):
    """The template contains no project files."""


def createproject(
    location: str,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    outputdir: Optional[pathlib.Path] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    outputdirisproject: bool = False,
    createrepository: bool = True,
    createconfigfile: bool = True,
) -> Optional[tuple[pathlib.Path, Repository]]:
    """Generate a project from a Cookiecutter template."""
    if outputdir is None:
        outputdir = pathlib.Path.cwd()

    template = loadtemplate(location, checkout, directory)
    config = loadcookiecutterconfig(location, template.path)
    render = createcookiecutterrenderer(template.path, config)
    bindings = bindcookiecuttervariables(
        config.variables,
        render,
        interactive=not no_input,
        bindings=extrabindings,
    )

    projectconfig = ProjectConfig(location, bindings, directory=directory)
    projectfiles = lazysequence(
        renderfiles(findcookiecutterpaths(template.path, config), render, bindings)
    )
    if not projectfiles:  # pragma: no cover
        raise EmptyTemplateError()

    projectname = projectfiles[0].path.parts[0]
    projectfiles2 = projectfiles.release()
    if createconfigfile:
        projectconfigfile = createprojectconfigfile(
            PurePath(projectname), projectconfig
        )
        projectfiles2 = itertools.chain(projectfiles2, [projectconfigfile])

    hookfiles = lazysequence(
        renderfiles(findcookiecutterhooks(template.path), render, bindings)
    )

    project_dir = outputdir if outputdirisproject else outputdir / projectname
    storage = createcookiecutterstorage(
        outputdir, project_dir, overwrite_if_exists, skip_if_file_exists, hookfiles
    )

    with storage:
        for projectfile in projectfiles2:
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)

    return project_dir, template


def create(
    location: str,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    outputdir: Optional[pathlib.Path] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    outputdirisproject: bool = False,
    createrepository: bool = True,
    createconfigfile: bool = True,
) -> None:
    """Generate a project from a Cookiecutter template."""
    try:
        result = createproject(
            location,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            outputdir=outputdir,
            directory=directory,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            outputdirisproject=outputdirisproject,
            createconfigfile=createconfigfile,
        )
        if result and createrepository:
            project_dir, template = result
            creategitrepository(project_dir, template.name, template.revision)
    except EmptyTemplateError:  # pragma: no cover
        pass
