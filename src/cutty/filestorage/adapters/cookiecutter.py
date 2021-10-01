"""File storage for Cookiecutter projects."""
import pathlib
from collections.abc import Iterable

from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.observers.cookiecutter import CookiecutterHooksObserver
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage


def createcookiecutterstorage(
    outputdir: pathlib.Path,
    projectdir: pathlib.Path,
    fileexists: FileExistsPolicy,
    hookfiles: Iterable[File],
) -> FileStorage:
    """Create storage for Cookiecutter project files."""
    storage: FileStorage = DiskFileStorage(outputdir, fileexists=fileexists)

    if hookfiles:  # pragma: no branch
        observer = CookiecutterHooksObserver(
            hookfiles=hookfiles, project=projectdir, fileexists=fileexists
        )
        storage = observe(storage, observer)

    return storage
