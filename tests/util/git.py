"""Git utilities."""
from pathlib import Path

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
