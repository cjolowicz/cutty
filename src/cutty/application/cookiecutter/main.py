"""Main entry point for the Cookiecutter compatibility layer."""
import functools
import pathlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

import appdirs
from yarl import URL

from cutty.application.cookiecutter.files import CookiecutterFileStorage
from cutty.application.cookiecutter.loader import loadconfig
from cutty.application.cookiecutter.loader import loadpaths
from cutty.application.cookiecutter.loader import loadrenderer
from cutty.filesystem.adapters.disk import DiskFilesystem
from cutty.filesystem.adapters.git import GitFilesystem
from cutty.filesystem.domain.path import Path
from cutty.repositories.adapters.git.repositories import GitRepository
from cutty.repositories.domain.cache import Cache
from cutty.templates.adapters.click.binders import prompt
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.services import render


def main(
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
    cache = Cache(
        pathlib.Path(appdirs.user_cache_dir("cutty")),
        providers=[GitRepository],
    )

    storage = CookiecutterFileStorage(
        pathlib.Path.cwd() if output_dir is None else output_dir,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    )

    templatedir = pathlib.Path(template)

    if not templatedir.is_dir():
        path = cache.get(URL(template), revision=checkout)
    elif templatedir.suffix == ".git" or (templatedir / ".git").is_dir():
        path = Path(filesystem=GitFilesystem(templatedir, *filter(None, [checkout])))
    else:
        path = Path(filesystem=DiskFilesystem(templatedir))

    if directory is not None:
        path = path.joinpath(*directory.parts)

    binder = override(
        binddefault if no_input else prompt,
        [Binding(key, value) for key, value in extra_context.items()],
    )

    render(
        path,
        loadconfig=functools.partial(loadconfig, template),
        loadrenderer=loadrenderer,
        loadpaths=loadpaths,
        renderbind=renderbindwith(binder),
        storefiles=storage.store,
    )
