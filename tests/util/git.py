"""Git utilities."""
import enum
from pathlib import Path
from textwrap import dedent

import pygit2

from cutty.util.git import commit as _commit


def commit(repository: pygit2.Repository, *, message: str = "") -> None:
    """Commit all changes in the repository."""
    signature = pygit2.Signature("you", "you@example.com")
    _commit(repository, message=message, signature=signature)


def move_repository_files_to_subdirectory(
    repository: pygit2.Repository, directory: str
) -> None:
    """Move all files in the repository to the given subdirectory."""
    builder = repository.TreeBuilder()
    builder.insert(directory, repository.head.peel().tree.id, pygit2.GIT_FILEMODE_TREE)
    tree = repository[builder.write()]
    repository.checkout_tree(tree)

    commit(repository, message=f"Move files to subdirectory {directory}")


def discoverrepository(path: Path) -> pygit2.Repository:
    """Discover a git repository."""
    while path.name and not path.exists():
        path = path.parent

    return pygit2.Repository(pygit2.discover_repository(path))


def updatefile(path: Path, text: str = "") -> None:
    """Add or update a repository file."""
    repository = discoverrepository(path)

    verb = "Update" if path.exists() else "Add"

    path.write_text(dedent(text).lstrip())

    commit(repository, message=f"{verb} {path.name}")


def updatefiles(paths: dict[Path, str]) -> None:
    """Add or update repository files."""
    verb = "Add"

    for path, text in paths.items():
        repository = discoverrepository(path)

        if path.exists():
            verb = "Update"

        path.write_text(dedent(text).lstrip())

    pathlist = " and ".join(path.name for path in paths)
    commit(repository, message=f"{verb} {pathlist}")


def appendfile(path: Path, text: str) -> None:
    """Append text to a repository file."""
    updatefile(path, path.read_text() + text)


def removefile(path: Path) -> None:
    """Remove a repository file."""
    repository = discoverrepository(path)

    path.unlink()

    commit(repository, message=f"Remove {path.name}")


class Side(enum.Enum):
    """The side of a conflict."""

    ANCESTOR = 0
    OURS = 1
    THEIRS = 2


def resolveconflicts(repository: pygit2.Repository, path: Path, side: Side) -> None:
    """Resolve the conflicts."""
    repositorypath = Path(
        repository.workdir if repository.workdir is not None else repository.path
    )
    pathstr = str(path.resolve().relative_to(repositorypath.resolve()))
    ancestor, ours, theirs = repository.index.conflicts[pathstr]
    resolution = (ancestor, ours, theirs)[side.value]

    del repository.index.conflicts[pathstr]

    repository.index.add(resolution)
    repository.index.write()
    repository.checkout(strategy=pygit2.GIT_CHECKOUT_FORCE, paths=[pathstr])
