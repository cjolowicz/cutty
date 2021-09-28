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


def updatecommitmessage(template: Template) -> str:
    """Return the commit message for updating the template."""
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: Template, action: str) -> str:
    """Return the commit message for linking the template."""
    if action == "link":
        return (
            f"Link to {template.name} {template.revision}"
            if template.revision
            else f"Link to {template.name}"
        )

    if action == "update":
        return (
            f"Update {template.name} to {template.revision}"
            if template.revision
            else f"Update {template.name}"
        )

    return (
        f"Initial import from {template.name} {template.revision}"
        if template.revision
        else f"Initial import from {template.name}"
    )
