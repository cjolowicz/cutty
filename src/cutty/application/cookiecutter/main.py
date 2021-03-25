"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from yarl import URL

from cutty.adapters.click.binders import prompt
from cutty.adapters.disk.files import DiskFileStorage
from cutty.application.cookiecutter.loader import loadconfig
from cutty.application.cookiecutter.loader import loadpaths
from cutty.application.cookiecutter.loader import loadrenderer
from cutty.domain.binders import renderbindwith
from cutty.domain.services import render
from cutty.repositories.adapters.git.repositories import GitRepository
from cutty.repositories.domain.cache import Cache


def main(url: str) -> None:
    """Generate a project from a Cookiecutter template."""
    cache = Cache(pathlib.Path("/tmp/cutty/cache"), providers=[GitRepository])
    storage = DiskFileStorage(pathlib.Path.cwd())
    path = cache.get(URL(url))
    render(
        path,
        loadconfig=loadconfig,
        loadrenderer=loadrenderer,
        loadpaths=loadpaths,
        renderbind=renderbindwith(prompt),
        storefiles=storage.store,
    )
