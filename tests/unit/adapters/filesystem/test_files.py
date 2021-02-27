"""Unit tests for cutty.adapters.filesystem.files."""
import pathlib

from cutty.adapters.filesystem.files import FilesystemFileStorage
from cutty.domain.files import File
from cutty.domain.paths import Path


def test_storage(tmp_path: pathlib.Path) -> None:
    """It stores the file."""
    path = Path.fromparts(["example", "README.md"])
    blob = "# example\n"
    file = File(path, blob)

    storage = FilesystemFileStorage(tmp_path)
    storage.store(file)

    assert blob == (tmp_path / "example" / "README.md").read_text()
