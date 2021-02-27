"""Unit tests for cutty.application.cookiecutter.templates."""
import pathlib

import pytest

from cutty.application.cookiecutter.templates import load
from cutty.domain.varspecs import DefaultVariableBuilder


def create(path: pathlib.Path, text: str) -> None:
    """Create a file with the given path and contents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def template_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a template directory."""
    create(
        tmp_path / "cookiecutter.json",
        '{"project": "example", "license": ["MIT", "GPL-3.0", "Apache-2.0"]}',
    )
    create(
        tmp_path / "{{ cookiecutter.project }}" / "README.md",
        "# {{ cookiecutter.project }}\n",
    )
    return tmp_path


def test_load(template_directory: pathlib.Path) -> None:
    """It loads a template."""
    template = load(template_directory)
    builder = DefaultVariableBuilder()
    variables = builder.build(template.variables)
    [readme] = [file.render(variables) for file in template.files]
    assert readme.path.parts == ("example", "README.md")
    assert readme.blob == "# example\n"
