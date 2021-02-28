"""Common fixtures."""
import pathlib
from textwrap import dedent

import pytest


def create(path: pathlib.Path, text: str) -> None:
    """Create a file with the given path and contents."""
    text = dedent(text).removeprefix("\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def template_directory(tmp_path: pathlib.Path) -> pathlib.Path:
    """Fixture for a template directory."""
    create(
        tmp_path / "cookiecutter.json",
        """
        {
          "project": "example",
          "license": ["MIT", "GPL-3.0", "Apache-2.0"],
          "_extensions": ["jinja2_time.TimeExtension"]
        }
        """,
    )

    create(
        tmp_path / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        """,
    )

    return tmp_path
