"""Unit tests for cutty.application.cookiecutter.templates."""
import pathlib

from cutty.application.cookiecutter.templates import load
from cutty.domain.templates import TemplateRenderer
from cutty.domain.varspecs import DefaultVariableBuilder


def test_load(template_directory: pathlib.Path) -> None:
    """It loads a template."""
    template = load(template_directory)
    renderer = TemplateRenderer(builder=DefaultVariableBuilder())
    [readme] = renderer.render(template)
    assert readme.path.parts == ("example", "README.md")
    assert readme.blob == "# example\n"
