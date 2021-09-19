"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

import platformdirs
from lazysequence import lazysequence

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.domain.files import File
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.repositories.domain.repository import Repository
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
        return

    if outputdirisproject:
        projectdir = outputdir
    else:
        projectdir = outputdir / projectfiles[0].path.parts[0]

    hookfiles = lazysequence(
        renderfiles(findcookiecutterhooks(template.path), render, bindings)
    )

    projectconfigfile: Optional[File]
    if createconfigfile:
        projectdir2 = PurePath(projectfiles[0].path.parts[0])
        if outputdirisproject:
            projectdir2 = PurePath()
        projectconfigfile = createprojectconfigfile(projectdir2, projectconfig)
    else:
        projectconfigfile = None

    projectfiles2 = projectfiles.release()
    with createcookiecutterstorage(
        outputdir,
        projectdir,
        overwrite_if_exists,
        skip_if_file_exists,
        hookfiles,
        createrepository,
        template.name,
        template.revision,
    ) as storage:
        for projectfile in projectfiles2:
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)

        if projectconfigfile is not None:
            storage.add(projectconfigfile)
