"""Main entry point for the Cookiecutter compatibility layer."""
from pathlib import Path

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter import templates
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.templates import TemplateRenderer


def main(directory: Path) -> None:
    """Generate a project from a Cookiecutter template."""
    renderer = TemplateRenderer(
        builder=PromptVariableBuilder(ClickPromptFactory()),
        storage=FilesystemFileStorage(Path.cwd()),
    )
    template = templates.load(directory)
    renderer.render(template)
