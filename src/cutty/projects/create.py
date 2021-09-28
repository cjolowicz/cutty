"""Creating projects from templates."""
from pathlib import Path

import pygit2

from cutty.projects.common import createcommitmessage
from cutty.projects.common import LATEST_BRANCH
from cutty.repositories.domain.repository import Repository as Template
from cutty.util import git


def creategitrepository(projectdir: Path, template: Template) -> None:
    """Create a git repository."""
    try:
        project = git.Repository.open(projectdir)
    except pygit2.GitError:
        project = git.Repository.init(projectdir)

    project.commit(message=createcommitmessage(template))
    project.heads[LATEST_BRANCH] = project.head.commit
