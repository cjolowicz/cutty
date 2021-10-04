"""Fixtures for cutty.projects."""
import pytest

from cutty.projects.template import Template


@pytest.fixture
def template() -> Template.Metadata:
    """Fixture for a `Template` instance."""
    location = "https://example.com/template"
    return Template.Metadata(location, None, None, "template", None)
