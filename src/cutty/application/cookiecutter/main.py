"""Main entry point for the Cookiecutter compatibility layer."""
from pathlib import Path

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter import templates
from cutty.domain.prompts import PromptVariableBuilder


def main(directory: Path) -> None:
    """Generate a project from a Cookiecutter template."""
    template = templates.load(directory)
    builder = PromptVariableBuilder(ClickPromptFactory())
    storage = FilesystemFileStorage(Path.cwd())
    for file in template.render(builder):
        storage.store(file)
