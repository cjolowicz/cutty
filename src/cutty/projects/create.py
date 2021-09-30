"""Creating projects from templates."""
from pathlib import Path

import pygit2

from cutty.projects.common import createcommitmessage
from cutty.projects.common import LATEST_BRANCH
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.loadtemplate import Template as Template2
from cutty.services.loadtemplate import TemplateMetadata
from cutty.util import git


def creategitrepository2(projectdir: Path, template: Template2) -> None:
    """Initialize the git repository for a project."""
    creategitrepository(projectdir, template.repository)


def creategitrepository(projectdir: Path, template: Template) -> None:
    """Initialize the git repository for a project."""
    try:
        project = git.Repository.open(projectdir)
    except pygit2.GitError:
        project = git.Repository.init(projectdir)

    metadata = TemplateMetadata("", None, None, template.name, template.revision)

    project.commit(message=createcommitmessage(metadata))
    project.heads[LATEST_BRANCH] = project.head.commit
