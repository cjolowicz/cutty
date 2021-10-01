"""Creating projects from templates."""
from pathlib import Path

import pygit2

from cutty.projects.common import createcommitmessage
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.loadtemplate import TemplateMetadata
from cutty.util import git


def creategitrepository(projectdir: Path, template: TemplateMetadata) -> None:
    """Initialize the git repository for a project."""
    try:
        project = git.Repository.open(projectdir)
    except pygit2.GitError:
        project = git.Repository.init(projectdir)

    project.commit(message=createcommitmessage(template))
    project.heads[LATEST_BRANCH] = project.head.commit
