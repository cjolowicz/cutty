"""Commit messages."""
from collections.abc import Callable

from cutty.projects.template import Template


MessageBuilder = Callable[[Template.Metadata], str]


def createcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for importing the project."""
    if template.commit2:
        return f"Import {template.name} {template.commit2.revision}"
    else:
        return f"Import {template.name}"


def updatecommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for updating the project."""
    if template.commit2:
        return f"Update {template.name} to {template.commit2.revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for linking the project."""
    if template.commit2:
        return f"Link to {template.name} {template.commit2.revision}"
    else:
        return f"Link to {template.name}"


def importcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for importing a template commit."""
    if template.commit2:
        return template.commit2.message
    else:  # pragma: no cover
        return updatecommitmessage(template)
