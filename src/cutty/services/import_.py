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
    config1 = replace(
        readprojectconfigfile(projectdir),
        revision="HEAD^" if revision is None else f"{revision}^",
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

    if commit != parent:
        try:
            repository.import_(commit)
        except MergeConflictError as error:
            try:
                resolveconflicts(projectdir, projectdir / "cutty.json", Side.THEIRS)
            except KeyError:
                pass

            repository.project._repository.index.read()
            if repository.project._repository.index.conflicts:
                message = str(error)
                paths = message.removeprefix("Merge conflicts: ").split(", ")
                if "cutty.json" in paths:
                    paths.remove("cutty.json")
                message = f"Merge conflicts: {', '.join(paths)}"
                raise MergeConflictError(message)
