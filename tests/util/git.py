"""Git utilities."""
import enum
from pathlib import Path
from textwrap import dedent

import pygit2

from cutty.util.git import Branch
from cutty.util.git import Repository


def createbranches(repository: Repository, *names: str) -> tuple[pygit2.Branch, ...]:
    """Create branches at HEAD."""
    return tuple(repository.createbranch(name) for name in names)


def createbranches2(repository: Repository, *names: str) -> tuple[Branch, ...]:
    """Create branches at HEAD."""
    return tuple(repository.branches.create(name) for name in names)


def move_repository_files_to_subdirectory(repositorypath: Path, directory: str) -> None:
    """Move all files in the repository to the given subdirectory."""
    subdirectory = repositorypath / directory
    for path in repositorypath.iterdir():
        if path.name != ".git":
            subdirectory.mkdir(exist_ok=True)
            path.rename(subdirectory / path.name)

    repository = Repository.open(repositorypath)
    repository.commit(message=f"Move files to subdirectory {directory}")


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
    """Resolve conflicts in the given file."""
    repository = pygit2.Repository(repositorypath)
    pathstr = str(path.relative_to(repositorypath))
    ancestor, ours, theirs = repository.index.conflicts[pathstr]
    resolution = (ancestor, ours, theirs)[side.value]

    del repository.index.conflicts[pathstr]

    repository.index.add(resolution)
    repository.index.write()
    repository.checkout(strategy=pygit2.GIT_CHECKOUT_FORCE, paths=[pathstr])
