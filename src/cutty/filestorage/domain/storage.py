"""File storage abstraction."""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Optional
from typing import TypeVar

from cutty.filestorage.domain.files import File


T = TypeVar("T", bound="FileStorage")


class FileStorage(abc.ABC):
    """Interface for file storage implementations."""

    @abc.abstractmethod
    def begin(self) -> None:
        """Begin a storage transaction."""

    @abc.abstractmethod
    def add(self, file: File) -> None:
        """Add the file to the storage."""

    @abc.abstractmethod
    def commit(self) -> None:
        """Commit all stores."""

    @abc.abstractmethod
    def rollback(self) -> None:
        """Rollback all stores."""

    def __enter__(self: T) -> T:
        """Enter the runtime context."""
        self.begin()
        return self

    def __exit__(
        self,
        exception_type: Optional[type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context."""
        if exception is None:
            self.commit()
        else:
            self.rollback()


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
