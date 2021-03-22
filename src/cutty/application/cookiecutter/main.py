"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from cutty.adapters.click.binders import prompt
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter.loader import CookiecutterRendererFactory
from cutty.application.cookiecutter.loader import CookiecutterTemplateConfigLoader
from cutty.application.cookiecutter.loader import loadfiles
from cutty.domain.binders import create_render_binder
from cutty.domain.services import RenderService
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def main(directory: pathlib.Path) -> None:
    """Generate a project from a Cookiecutter template."""
    path = Path(filesystem=DiskFilesystem(directory))
    storage = FilesystemFileStorage(pathlib.Path.cwd())
    service = RenderService(
        configloader=CookiecutterTemplateConfigLoader(),
        rendererfactory=CookiecutterRendererFactory(),
        loadfiles=loadfiles,
        renderbind=create_render_binder(prompt),
        storefile=storage.store,
    )
    service.render(path)
