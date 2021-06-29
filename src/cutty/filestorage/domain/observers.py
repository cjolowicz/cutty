"""File storage observers."""
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorage


class FileStorageObserver:
    """Base class for file storage observers."""

    def begin(self) -> None:
        """A storage transaction was started."""

    def add(self, file: File) -> None:
        """A file was added to the transaction."""

    def commit(self) -> None:
        """A storage transaction was completed."""

    def rollback(self) -> None:
        """A storage transaction was aborted."""


def observe(storage: FileStorage, observer: FileStorageObserver) -> FileStorage:
    """Wrap a storage with an observer."""

    class _ObservableFileStorage(FileStorage):
        def begin(self) -> None:
            storage.begin()
            observer.begin()

        def add(self, file: File) -> None:
            storage.add(file)
            observer.add(file)

        def commit(self) -> None:
            storage.commit()
            observer.commit()

        def rollback(self) -> None:
            storage.rollback()
            observer.rollback()

    return _ObservableFileStorage()
