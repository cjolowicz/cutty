"""File storage for Cookiecutter projects."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.observers.cookiecutter import CookiecutterHooksObserver
from cutty.filestorage.adapters.observers.git import GitRepositoryObserver
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage


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
    outputdir: pathlib.Path,
    project_dir: pathlib.Path,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    hookfiles: Sequence[File],
    createrepository: bool,
    template: str = "template",
    revision: Optional[str] = None,
) -> FileStorage:
    """Create storage for Cookiecutter project files."""
    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    storage: FileStorage = DiskFileStorage(outputdir, fileexists=fileexists)

    if hookfiles:  # pragma: no branch
        observer = CookiecutterHooksObserver(
            hookfiles=hookfiles, project=project_dir, fileexists=fileexists
        )
        storage = observe(storage, observer)

    if createrepository:
        storage = observe(
            storage,
            GitRepositoryObserver(
                project=project_dir, template=template, revision=revision
            ),
        )

    return storage
