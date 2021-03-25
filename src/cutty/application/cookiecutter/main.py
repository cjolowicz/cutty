"""Main entry point for the Cookiecutter compatibility layer."""
import functools
import pathlib
from typing import Optional

import appdirs
from yarl import URL

from cutty.adapters.click.binders import prompt
from cutty.application.cookiecutter.files import CookiecutterFileStorage
from cutty.application.cookiecutter.loader import loadconfig
from cutty.application.cookiecutter.loader import loadpaths
from cutty.application.cookiecutter.loader import loadrenderer
from cutty.domain.binders import binddefault
from cutty.domain.binders import renderbindwith
from cutty.domain.services import render
from cutty.repositories.adapters.git.repositories import GitRepository
from cutty.repositories.domain.cache import Cache


def main(
    url: str,
    *,
    interactive: bool = True,
    checkout: Optional[str] = None,
    output_dir: Optional[pathlib.Path] = None,
) -> None:
    """Generate a project from a Cookiecutter template."""
    cache = Cache(
        pathlib.Path(appdirs.user_cache_dir("cutty")),
        providers=[GitRepository],
    )
    storage = CookiecutterFileStorage(
        pathlib.Path.cwd() if output_dir is None else output_dir
    )
    path = cache.get(URL(url), revision=checkout)
    render(
        path,
        loadconfig=functools.partial(loadconfig, url),
        loadrenderer=loadrenderer,
        loadpaths=loadpaths,
        renderbind=renderbindwith(prompt if interactive else binddefault),
        storefiles=storage.store,
    )
