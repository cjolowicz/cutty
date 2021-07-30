"""Git utilities."""
import enum
from pathlib import Path
from textwrap import dedent

import pygit2

from cutty.util.git import createbranch
from cutty.util.git import Repository


def createbranches(
    repository: pygit2.Repository, *names: str
) -> tuple[pygit2.Branch, ...]:
    """Create branches at HEAD."""
    return tuple(createbranch(repository, name) for name in names)


def move_repository_files_to_subdirectory(repositorypath: Path, directory: str) -> None:
    """Move all files in the repository to the given subdirectory."""
    repository = Repository.open(repositorypath).repository
    builder = repository.TreeBuilder()
    builder.insert(directory, repository.head.peel().tree.id, pygit2.GIT_FILEMODE_TREE)
    tree = repository[builder.write()]
    repository.checkout_tree(tree)

    Repository(repository).commit(message=f"Move files to subdirectory {directory}")


def locaterepository(path: Path) -> Repository:
    """Locate the git repository containing the given path."""
    while path.name and not path.exists():
        path = path.parent

    repository = Repository.discover(path)
    assert repository is not None
    return repository


def updatefile(path: Path, text: str = "") -> None:
    """Add or update a repository file."""
    repository = locaterepository(path)

    verb = "Update" if path.exists() else "Add"

    path.write_text(dedent(text).lstrip())

    repository.commit(message=f"{verb} {path.name}")


def updatefiles(paths: dict[Path, str]) -> None:
    """Add or update repository files."""
    if not paths:
        return

    verb = "Add"

    for path, text in paths.items():
        repository = locaterepository(path)

        if path.exists():
            verb = "Update"

        path.write_text(dedent(text).lstrip())

    pathlist = " and ".join(path.name for path in paths)
    repository.commit(message=f"{verb} {pathlist}")


def appendfile(path: Path, text: str) -> None:
    """Append text to a repository file."""
    updatefile(path, path.read_text() + text)


def removefile(path: Path) -> None:
    """Remove a repository file."""
    repository = locaterepository(path)

    path.unlink()

    repository.commit(message=f"Remove {path.name}")


class Side(enum.Enum):
    """The side of a conflict."""

    ANCESTOR = 0
    OURS = 1
    THEIRS = 2


def resolveconflicts(repositorypath: Path, path: Path, side: Side) -> None:
    """Resolve the conflicts."""
    repository = Repository.open(repositorypath).repository
    pathstr = str(path.relative_to(repositorypath))
    ancestor, ours, theirs = repository.index.conflicts[pathstr]
    resolution = (ancestor, ours, theirs)[side.value]

    del repository.index.conflicts[pathstr]

    repository.index.add(resolution)
    repository.index.write()
    repository.checkout(strategy=pygit2.GIT_CHECKOUT_FORCE, paths=[pathstr])
