"""Main entry point for the Cookiecutter compatibility layer."""
import pathlib

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.adapters.filesystem.filesystem import DiskFilesystem
from cutty.application.cookiecutter.loader import CookiecutterFileLoader
from cutty.application.cookiecutter.loader import CookiecutterRenderableLoaderFactory
from cutty.application.cookiecutter.loader import (
    CookiecutterVariableSpecificationLoader,
)
from cutty.domain.loader import TemplateLoader
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.templates import TemplateRenderer


def main(directory: pathlib.Path) -> None:
    """Generate a project from a Cookiecutter template."""
    filesystem = DiskFilesystem(directory)
    loader = TemplateLoader(
        loaderfactory=CookiecutterRenderableLoaderFactory(),
        varloader=CookiecutterVariableSpecificationLoader(),
        fileloader=CookiecutterFileLoader(),
    )
    renderer = TemplateRenderer(
        builder=PromptVariableBuilder(ClickPromptFactory()),
        storage=FilesystemFileStorage(pathlib.Path.cwd()),
    )
    template = loader.load(filesystem.root)
    renderer.render(template)
