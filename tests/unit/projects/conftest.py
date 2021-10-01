"""Fixtures for cutty.projects."""
import pathlib

import pytest

from cutty.projects.common import GenerateProject
from cutty.projects.template import TemplateMetadata


@pytest.fixture
def template() -> TemplateMetadata:
    """Fixture for a `Template` instance."""
    location = "https://example.com/template"
    return TemplateMetadata(location, None, None, "template", None)


@pytest.fixture
def generateproject() -> GenerateProject:
    """Fixture for a `generateproject` function."""

    def _(project: pathlib.Path) -> None:
        (project / "cutty.json").touch()

    return _
