"""File storage for Cookiecutter projects."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.observers.cookiecutter import CookiecutterHooksObserver
from cutty.filestorage.adapters.observers.git import GitRepositoryObserver
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.path import Path


def fileexistspolicy(
    overwrite_if_exists: bool, skip_if_file_exists: bool
) -> FileExistsPolicy:
    """Return the policy for overwriting existing files."""
    return (
        FileExistsPolicy.RAISE
        if not overwrite_if_exists
        else FileExistsPolicy.SKIP
        if skip_if_file_exists
        else FileExistsPolicy.OVERWRITE
    )


def createcookiecutterstorage(
    template_dir: Path,
    project_dir: pathlib.Path,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    hookfiles: Sequence[File],
) -> FileStorage:
    """Create storage for Cookiecutter project files."""
    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    storage: FileStorage = DiskFileStorage(project_dir.parent, fileexists=fileexists)

    observer: Optional[FileStorageObserver] = None

    if hookfiles:  # pragma: no branch
        observer = CookiecutterHooksObserver(
            hookfiles=hookfiles, project=project_dir, fileexists=fileexists
        )

    if observer:  # pragma: no branch
        storage = observe(storage, observer)

    storage = observe(storage, GitRepositoryObserver(project=project_dir))

    return storage
