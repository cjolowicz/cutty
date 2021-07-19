"""Git utilities."""
import pygit2

from cutty.filestorage.adapters.observers.git import commit as _commit


def commit(repository: pygit2.Repository, *, message: str) -> None:
    """Commit all changes in the repository."""
    signature = pygit2.Signature("you", "you@example.com")
    _commit(repository, message=message, signature=signature)
