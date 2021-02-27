"""Main entry point for the Cookiecutter compatibility layer."""
import contextlib
from pathlib import Path

from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.application.cookiecutter import templates
from cutty.domain.paths import EmptyPathComponent
from cutty.domain.prompts import PromptVariableBuilder


def main(directory: Path) -> None:
    """Generate a project from a Cookiecutter template."""
    template = templates.load(directory)
    builder = PromptVariableBuilder(ClickPromptFactory())
    variables = builder.build(template.variables)
    storage = FilesystemFileStorage(Path.cwd())
    for renderable in template.files:
        with contextlib.suppress(EmptyPathComponent):
            file = renderable.render(variables)
            storage.store(file)
