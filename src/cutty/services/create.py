"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

import platformdirs
from lazysequence import lazysequence

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.adapters.cookiecutter.config import findcookiecutterhooks
from cutty.templates.adapters.cookiecutter.config import findcookiecutterpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.projectconfig import createprojectconfigfile
from cutty.templates.adapters.cookiecutter.projectconfig import ProjectConfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.renderfiles import renderfiles


def create(
    template: str,
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
    cachedir = pathlib.Path(platformdirs.user_cache_dir("cutty"))
    templatedir = getdefaultrepositoryprovider(cachedir)(template, revision=checkout)

    if directory is not None:
        templatedir = templatedir.joinpath(*directory.parts)

    if outputdir is None:
        outputdir = pathlib.Path.cwd()

    config = loadcookiecutterconfig(template, templatedir)
    render = createcookiecutterrenderer(templatedir, config)
    bindings = bindcookiecuttervariables(
        config.variables,
        render,
        interactive=not no_input,
        bindings=extrabindings,
    )

    projectfiles = lazysequence(
        renderfiles(findcookiecutterpaths(templatedir, config), render, bindings)
    )
    if not projectfiles:  # pragma: no cover
        return

    strip = 0 if directory is None else len(directory.parts)

    if outputdirisproject:
        projectdir = outputdir
        strip += 1
    else:
        projectdir = outputdir / projectfiles[0].path.parts[strip]

    hookfiles = lazysequence(
        renderfiles(findcookiecutterhooks(templatedir), render, bindings)
    )
    projectconfigfile = (
        createprojectconfigfile(
            PurePath(*projectdir.relative_to(outputdir).parts),
            ProjectConfig(template, bindings, directory=directory),
        )
        if createconfigfile
        else None
    )

    with createcookiecutterstorage(
        outputdir,
        projectdir,
        overwrite_if_exists,
        skip_if_file_exists,
        hookfiles,
        createrepository,
    ) as storage:
        for projectfile in projectfiles.release():
            if strip:
                path = PurePath(*projectfile.path.parts[strip:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)

        if projectconfigfile is not None:
            storage.add(projectconfigfile)
