"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from cutty.adapters.click.binders import prompt
from cutty.adapters.disk.files import DiskFileStorage
from cutty.adapters.disk.hooks import executehook
from cutty.application.cookiecutter.loader import loadconfig
from cutty.application.cookiecutter.loader import loadhooks
from cutty.application.cookiecutter.loader import loadpaths
from cutty.application.cookiecutter.loader import loadrenderer
from cutty.domain.binders import renderbindwith
from cutty.domain.services import render
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def main(directory: pathlib.Path) -> None:
    """Generate a project from a Cookiecutter template."""
    path = Path(filesystem=DiskFilesystem(directory))
    storage = DiskFileStorage(pathlib.Path.cwd())
    render(
        path,
        loadconfig=loadconfig,
        loadrenderer=loadrenderer,
        loadpaths=loadpaths,
        loadhooks=loadhooks,
        renderbind=renderbindwith(prompt),
        storefile=storage.store,
        executehook=executehook,
    )
