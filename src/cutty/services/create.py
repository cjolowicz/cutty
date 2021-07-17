"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

import appdirs
from lazysequence import lazysequence

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.adapters.cookiecutter.config import findhooks
from cutty.templates.adapters.cookiecutter.config import findpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.renderfiles import renderfiles


def create(
    template: str,
    *,
    extra_context: Mapping[str, str] = MappingProxyType({}),
    no_input: bool = False,
    checkout: Optional[str] = None,
    outputdir: Optional[pathlib.Path] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    outputdirisproject: bool = False,
) -> None:
    """Generate a project from a Cookiecutter template."""
    cachedir = pathlib.Path(appdirs.user_cache_dir("cutty"))
    templatedir = getdefaultrepositoryprovider(cachedir)(template, revision=checkout)

    if directory is not None:
        templatedir = templatedir.joinpath(*directory.parts)  # pragma: no cover

    if outputdir is None:  # pragma: no branch
        outputdir = pathlib.Path.cwd()

    config = loadcookiecutterconfig(template, templatedir)
    render = createcookiecutterrenderer(templatedir, config)
    bindings = bindcookiecuttervariables(
        config.variables,
        render,
        interactive=not no_input,
        bindings=[Binding(key, value) for key, value in extra_context.items()],
    )

    projectfiles = lazysequence(
        renderfiles(findpaths(templatedir, config), render, bindings)
    )
    if not projectfiles:  # pragma: no cover
        return

    if outputdirisproject:
        projectdir = outputdir
    else:
        projectdir = outputdir / projectfiles[0].path.parts[0]

    hookfiles = lazysequence(renderfiles(findhooks(templatedir), render, bindings))

    with createcookiecutterstorage(
        outputdir,
        projectdir,
        overwrite_if_exists,
        skip_if_file_exists,
        hookfiles,
    ) as storage:
        for projectfile in projectfiles.release():
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)
            storage.add(projectfile)
