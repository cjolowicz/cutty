"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from cutty.adapters.click.binders import prompt
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter.loader import CookiecutterFileLoader
from cutty.application.cookiecutter.loader import CookiecutterRendererFactory
from cutty.application.cookiecutter.loader import CookiecutterTemplateConfigLoader
from cutty.domain.binders import create_binder
from cutty.domain.services import RenderService
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def main(directory: pathlib.Path) -> None:
    """Generate a project from a Cookiecutter template."""
    service = RenderService(
        configloader=CookiecutterTemplateConfigLoader(),
        rendererfactory=CookiecutterRendererFactory(),
        fileloader=CookiecutterFileLoader(),
        bind=create_binder(prompt),
        storage=FilesystemFileStorage(pathlib.Path.cwd()),
    )
    path = Path(filesystem=DiskFilesystem(directory))
    service.render(path)
