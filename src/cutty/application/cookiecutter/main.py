"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter.loader import CookiecutterFileLoader
from cutty.application.cookiecutter.loader import CookiecutterRenderableLoaderFactory
from cutty.application.cookiecutter.loader import CookiecutterTemplateConfigLoader
from cutty.domain.loader import TemplateLoader
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.templates import TemplateRenderer
from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def main(directory: pathlib.Path) -> None:
    """Generate a project from a Cookiecutter template."""
    path = Path(filesystem=DiskFilesystem(directory))
    loader = TemplateLoader(
        configloader=CookiecutterTemplateConfigLoader(),
        loaderfactory=CookiecutterRenderableLoaderFactory(),
        fileloader=CookiecutterFileLoader(),
    )
    renderer = TemplateRenderer(
        builder=PromptVariableBuilder(ClickPromptFactory()),
        storage=FilesystemFileStorage(pathlib.Path.cwd()),
    )
    template = loader.load(path)
    renderer.render(template)
