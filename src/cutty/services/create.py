"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

import appdirs

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.domain.files import File
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.adapters.cookiecutter.config import findhooks
from cutty.templates.adapters.cookiecutter.config import findpaths
from cutty.templates.adapters.cookiecutter.config import loadcookiecutterconfig
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.renderfiles import renderfiles
from cutty.util.lazysequence import LazySequence


def get_project_dir(output_dir: Optional[pathlib.Path], file: File) -> pathlib.Path:
    """Determine the location of the generated project."""
    parent = output_dir if output_dir is not None else pathlib.Path.cwd()
    return parent / file.path.parts[0]


def create(
    template: str,
    *,
    extra_context: Mapping[str, str] = MappingProxyType({}),
    no_input: bool = False,
    checkout: Optional[str] = None,
    output_dir: Optional[pathlib.Path] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> None:
    """Generate a project from a Cookiecutter template."""
    cachedir = pathlib.Path(appdirs.user_cache_dir("cutty"))
    template_dir = getdefaultrepositoryprovider(cachedir)(template, revision=checkout)

    if directory is not None:
        template_dir = template_dir.joinpath(*directory.parts)  # pragma: no cover

    config = loadcookiecutterconfig(template, template_dir)
    render = createcookiecutterrenderer(template_dir, config)
    bindings = bindcookiecuttervariables(
        config.variables,
        render,
        interactive=not no_input,
        bindings=[Binding(key, value) for key, value in extra_context.items()],
    )

    projectfiles = LazySequence(
        renderfiles(findpaths(template_dir, config), render, bindings)
    )
    if not projectfiles:  # pragma: no cover
        return

    project_dir = get_project_dir(output_dir, projectfiles[0])
    hookfiles = LazySequence(renderfiles(findhooks(template_dir), render, bindings))

    with createcookiecutterstorage(
        template_dir,
        project_dir,
        overwrite_if_exists,
        skip_if_file_exists,
        hookfiles,
    ) as storage:
        for projectfile in projectfiles.release():
            storage.add(projectfile)
