"""File storage abstraction."""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Optional
from typing import TypeVar

from cutty.filestorage.domain.files import File


T = TypeVar("T", bound="FileStorageABC")


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


class FileStorageABC(abc.ABC):
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


class ObservableFileStorage(FileStorageABC):
    """Storage wrapper with observers."""

    def __init__(self, storage: FileStorageABC) -> None:
        """Initialize."""
        self.storage = storage
        self.observers: list[FileStorageObserver] = []

    def begin(self) -> None:
        """Begin a storage transaction."""
        self.storage.begin()
        for observer in self.observers:
            observer.begin()

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        self.storage.add(file)
        for observer in self.observers:
            observer.add(file)

    def commit(self) -> None:
        """Commit all stores."""
        self.storage.commit()
        for observer in self.observers:
            observer.commit()

    def rollback(self) -> None:
        """Rollback all stores."""
        self.storage.rollback()
        for observer in self.observers:
            observer.rollback()


class FileStorage(FileStorageABC):
    """Interface for file storage implementations."""

    def __init__(self) -> None:
        """Initialize."""
        self.observers: list[FileStorageObserver] = []

    def begin(self) -> None:
        """Begin a storage transaction."""
        for observer in self.observers:
            observer.begin()

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        self._add(file)
        for observer in self.observers:
            observer.add(file)

    @abc.abstractmethod
    def _add(self, file: File) -> None:
        """Add the file to the storage."""

    def commit(self) -> None:
        """Commit all stores."""

    def __exit__(
        self,
        exception_type: Optional[type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context."""
        if exception is None:
            self.commit()
            for observer in self.observers:
                observer.commit()
        else:
            self.rollback()
            for observer in self.observers:
                observer.rollback()
