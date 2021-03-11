"""Unit tests for cutty.application.cookiecutter.templates."""
import pathlib

from cutty.application.cookiecutter.templates import load
from cutty.domain.files import renderfiles
from cutty.domain.varspecs import DefaultVariableBuilder


def test_load(template_directory: pathlib.Path) -> None:
    """It loads a template."""
    template = load(template_directory)
    variables = DefaultVariableBuilder().build(template.variables)
    [readme] = renderfiles(template.files, variables)
    assert readme.path.parts == ("example", "README.md")
    assert readme.read() == "# example\n"
