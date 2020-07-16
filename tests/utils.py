"""Test utilities."""
from cutty import git


def commit(repository: git.Repository) -> str:
    """Create an empty commit and return the SHA1 hash."""
    repository.git("commit", "--allow-empty", "--allow-empty-message", "--message=")
    return repository.rev_parse("HEAD")
