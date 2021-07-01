"""File storage for Cookiecutter projects."""
import pathlib
from collections.abc import Sequence

from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.path import Path


def createcookiecutterstorage(
    template_dir: Path,
    project_dir: pathlib.Path,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    hookfiles: Sequence[File],
) -> FileStorage:
    """Create storage for Cookiecutter project files."""
    from cutty.services.create import createstorage

    return createstorage(
        template_dir, project_dir, overwrite_if_exists, skip_if_file_exists, hookfiles
    )
