"""Git utilities."""
from pathlib import Path
from textwrap import dedent

import pygit2

from cutty.filestorage.adapters.observers.git import commit as _commit


def commit(repositorypath: Path, *, message: str) -> None:
    """Commit all changes in the repository."""
    repository = pygit2.Repository(repositorypath)
    signature = pygit2.Signature("you", "you@example.com")
    _commit(repository, message=message, signature=signature)


def move_repository_files_to_subdirectory(repositorypath: Path, directory: str) -> None:
    """Move all files in the repository to the given subdirectory."""
    repository = pygit2.Repository(repositorypath)
    builder = repository.TreeBuilder()
    builder.insert(directory, repository.head.peel().tree.id, pygit2.GIT_FILEMODE_TREE)
    tree = repository[builder.write()]
    repository.checkout_tree(tree)

    commit(repositorypath, message=f"Move files to subdirectory {directory}")


def discoverrepository(path: Path) -> Path:
    """Discover a git repository."""
    while path.name and not path.exists():
        path = path.parent

    return Path(pygit2.discover_repository(path))


def updatefile(path: Path, text: str) -> None:
    """Add or update a repository file."""
    repository = discoverrepository(path)

    verb = "Update" if path.exists() else "Add"

    path.write_text(dedent(text).lstrip())

    commit(repository, message=f"{verb} {path.name}")


def removefile(path: Path) -> None:
    """Remove a repository file."""
    repository = discoverrepository(path)

    path.unlink()

    commit(repository, message=f"Remove {path.name}")
