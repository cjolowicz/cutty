"""Fixtures for cutty.projects."""
import pytest

from cutty.projects.template import Template


@pytest.fixture
def template() -> Template.Metadata:
    """Fixture for a `Template.Metadata` instance."""
    location = "https://example.com/template"
    return Template.Metadata(location, "template", None, None)
