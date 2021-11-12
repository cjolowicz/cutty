"""Fixtures for cutty.projects."""
import datetime

import pytest

from cutty.packages.domain.package import Author
from cutty.packages.domain.package import Commit
from cutty.projects.template import Template


@pytest.fixture
def template() -> Template.Metadata:
    """Fixture for a `Template.Metadata` instance."""
    location = "https://example.com/template"
    return Template.Metadata(location, None, "template")


@pytest.fixture
def commit() -> Commit:
    """Fixture for a `Commit` instance."""
    return Commit(
        "f4c0629d635865697b3e99b5ca581e78b2c7d976",
        "v1.0.0",
        "Release 1.0.0",
        Author("You", "you@example.com"),
        datetime.datetime.now(datetime.timezone.utc),
    )
