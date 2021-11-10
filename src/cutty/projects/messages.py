"""Commit messages."""
from collections.abc import Callable

from cutty.projects.template import Template


MessageBuilder = Callable[[Template.Metadata], str]


def createcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for importing the project."""
    revision = None if template.commit2 is None else template.commit2.revision
    if revision:
        return f"Import {template.name} {revision}"
    else:
        return f"Import {template.name}"


def updatecommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for updating the project."""
    revision = None if template.commit2 is None else template.commit2.revision
    if revision:
        return f"Update {template.name} to {revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for linking the project."""
    revision = None if template.commit2 is None else template.commit2.revision
    if revision:
        return f"Link to {template.name} {revision}"
    else:
        return f"Link to {template.name}"


def importcommitmessage(template: Template.Metadata) -> str:
    """Build the commit message for importing a template commit."""
    if template.message:
        return template.message
    else:  # pragma: no cover
        return updatecommitmessage(template)
