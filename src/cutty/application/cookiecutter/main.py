"""Main entry point for the Cookiecutter compatibility layer."""
from pathlib import Path

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter import templates
from cutty.domain.files import renderfiles
from cutty.domain.prompts import PromptVariableBuilder


def main(directory: Path) -> None:
    """Generate a project from a Cookiecutter template."""
    template = templates.load(directory)
    builder = PromptVariableBuilder(ClickPromptFactory())
    storage = FilesystemFileStorage(Path.cwd())
    variables = builder.build(template.variables)
    for file in renderfiles(template.files, variables):
        storage.store(file)
