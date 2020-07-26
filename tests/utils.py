"""Test utilities."""
from cutty import git


def commit(repository: git.Repository) -> str:
    """Create an empty commit and return the SHA1 hash."""
    repository.commit(allow_empty=True, allow_empty_message=True, message="")
    return repository.rev_parse("HEAD")
