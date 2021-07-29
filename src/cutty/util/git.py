"""Git utilities."""
import contextlib
import os
from pathlib import Path
from typing import Optional

import pygit2


def default_signature(repository: pygit2.Repository) -> pygit2.Signature:
    """Return the default signature."""
    with contextlib.suppress(KeyError):
        return pygit2.Signature(
            os.environ["GIT_AUTHOR_NAME"],
            os.environ["GIT_AUTHOR_EMAIL"],
        )
    return repository.default_signature  # pragma: no cover


def commit(
    repository: pygit2.Repository,
    *,
    message: str,
    signature: Optional[pygit2.Signature] = None,
) -> None:
    """Commit all changes in the repository.

    If there are no changes relative to the parent, this is a noop.
    """
    repository.index.add_all()

    tree = repository.index.write_tree()
    if not repository.head_is_unborn and tree == repository.head.peel().tree.id:
        return

    repository.index.write()

    if signature is None:
        signature = default_signature(repository)

    parents = [] if repository.head_is_unborn else [repository.head.target]
    repository.create_commit("HEAD", signature, signature, message, tree, parents)


def checkoutemptytree(repositorypath: Path) -> None:
    """Check out an empty tree from the repository."""
    repository = pygit2.Repository(repositorypath)
    oid = repository.TreeBuilder().write()
    repository.checkout_tree(repository[oid])
