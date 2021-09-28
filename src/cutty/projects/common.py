"""Common functionality for projects."""
from collections.abc import Callable
from pathlib import Path

from cutty.repositories.domain.repository import Repository as Template


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


CreateProject = Callable[[Path], Template]


def commitmessage(template: Template) -> str:
    """Return the commit message for importing the template."""
    if template.revision:
        return f"Initial import from {template.name} {template.revision}"
    else:
        return f"Initial import from {template.name}"
