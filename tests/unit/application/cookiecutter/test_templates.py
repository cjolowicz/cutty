"""Unit tests for cutty.application.cookiecutter.templates."""
import pathlib

from cutty.application.cookiecutter.templates import load
from cutty.domain.varspecs import DefaultVariableBuilder


def test_load(template_directory: pathlib.Path) -> None:
    """It loads a template."""
    template = load(template_directory)
    builder = DefaultVariableBuilder()
    variables = builder.build(template.variables)
    [readme] = [file.render(variables) for file in template.files]
    assert readme.path.parts == ("example", "README.md")
    assert readme.blob == "# example\n"
