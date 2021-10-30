"""Import changes from templates into projects."""
import enum
from dataclasses import replace
from pathlib import Path
from typing import Optional

import pygit2

from cutty.packages.adapters.providers.git import RevisionNotFoundError
from cutty.projects.build import buildproject
from cutty.projects.config import ProjectConfig
from cutty.projects.config import readprojectconfigfile
from cutty.projects.messages import updatecommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.util.git import MergeConflictError


class Side(enum.Enum):
    """The side of a conflict."""

    ANCESTOR = 0
    OURS = 1
    THEIRS = 2


def resolveconflicts(repositorypath: Path, path: Path, side: Side) -> None:
    """Resolve conflicts in the given file."""
    repository = pygit2.Repository(repositorypath)
    pathstr = str(path.relative_to(repositorypath))
    ancestor, ours, theirs = repository.index.conflicts[pathstr]
    resolution = (ancestor, ours, theirs)[side.value]

    del repository.index.conflicts[pathstr]

    repository.index.add(resolution)
    repository.index.write()
    repository.checkout(strategy=pygit2.GIT_CHECKOUT_FORCE, paths=[pathstr])


def import_(projectdir: Path, *, revision: Optional[str]) -> None:
    """Import changes from a template into a project."""
    config1 = readprojectconfigfile(projectdir)
    config1 = replace(
        config1,
        revision="HEAD^" if revision is None else f"{revision}^",  # FIXME: git-specific
    )

    config2 = ProjectConfig(
        config1.template,
        config1.bindings,
        revision,
        config1.directory,
    )

    repository = ProjectRepository(projectdir)

    parent: Optional[str]
    try:
        parent = buildproject(
            repository,
            config1,
            interactive=True,
            commitmessage=updatecommitmessage,
        )
    except RevisionNotFoundError:
        parent = None

    commit = buildproject(
        repository,
        config2,
        interactive=True,
        commitmessage=updatecommitmessage,
        parent=parent,
    )

    # If `commit` and `parent` are identical then so is the template revision
    # stored in their cutty.json. But for the version control systems we
    # support, commits never have the same hash as their parents.
    assert commit != parent  # noqa: S101

    try:
        repository.import_(commit)
    except MergeConflictError:
        try:
            resolveconflicts(projectdir, projectdir / "cutty.json", Side.THEIRS)
        except KeyError:
            pass

        index = repository.project._repository.index
        index.read()

        if index.conflicts:
            raise MergeConflictError.fromindex(index)

        repository.continue_()
