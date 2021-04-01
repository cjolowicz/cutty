"""Common fixtures."""
import os
import pathlib
from textwrap import dedent

import pytest
from _pytest.config import Config
from hypothesis import settings


def pytest_configure(config: Config) -> None:
    """Load the hypothesis profile."""
    settings.register_profile("fast", max_examples=1)
    settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))


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
          "cli": true,
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
