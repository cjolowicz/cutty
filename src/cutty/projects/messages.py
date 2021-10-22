"""Commit messages."""
from cutty.projects.template import Template


def createcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for importing the project."""
    if template.revision:
        return f"Initial import from {template.name} {template.revision}"
    else:
        return f"Initial import from {template.name}"


def updatecommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for updating the project."""
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for linking the project."""
    if template.revision:
        return f"Link to {template.name} {template.revision}"
    else:
        return f"Link to {template.name}"
