"""Common functionality for projects."""
from collections.abc import Callable
from pathlib import Path

from cutty.projects.loadtemplate import TemplateMetadata


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


GenerateProject = Callable[[Path], None]


def createcommitmessage(template: TemplateMetadata) -> str:
    """Return the commit message for importing the template."""
    if template.revision:
        return f"Initial import from {template.name} {template.revision}"
    else:
        return f"Initial import from {template.name}"


def updatecommitmessage(template: TemplateMetadata) -> str:
    """Return the commit message for updating the template."""
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: TemplateMetadata) -> str:
    """Return the commit message for linking the template."""
    if template.revision:
        return f"Link to {template.name} {template.revision}"
    else:
        return f"Link to {template.name}"
