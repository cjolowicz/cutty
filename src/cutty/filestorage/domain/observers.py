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


class _ObservableFileStorage(FileStorage):
    """Storage wrapper with an observer."""

    def __init__(self, storage: FileStorage, observer: FileStorageObserver) -> None:
        """Initialize."""
        self.storage = storage
        self.observer = observer

    def begin(self) -> None:
        """Begin a storage transaction."""
        self.storage.begin()
        self.observer.begin()

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        self.storage.add(file)
        self.observer.add(file)

    def commit(self) -> None:
        """Commit all stores."""
        self.storage.commit()
        self.observer.commit()

    def rollback(self) -> None:
        """Rollback all stores."""
        self.storage.rollback()
        self.observer.rollback()


def observe(storage: FileStorage, observer: FileStorageObserver) -> FileStorage:
    """Wrap a storage with an observer."""
    return _ObservableFileStorage(storage, observer)
