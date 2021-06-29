"""File storage abstraction."""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Generic
from typing import Optional
from typing import TypeVar

from cutty.filestorage.domain.files import File


T = TypeVar("T", bound="FileStorage")


class FileStorageObserver:
    """Base class for file storage observers."""

    def begin(self) -> None:
        """A storage transaction was started."""

    def commit(self) -> None:
        """A storage transaction was completed."""

    def rollback(self) -> None:
        """A storage transaction was aborted."""


class FileStorage(abc.ABC):
    """Interface for file storage implementations."""

    @abc.abstractmethod
    def add(self, file: File) -> None:
        """Add the file to the storage."""

    def commit(self) -> None:
        """Commit all stores."""

    @abc.abstractmethod
    def rollback(self) -> None:
        """Rollback all stores."""

    def __enter__(self: T) -> T:
        """Enter the runtime context."""
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


class FileStorageWrapper(FileStorage, Generic[T]):
    """Wrapper for file storage implementations."""

    def __init__(self, storage: T) -> None:
        """Initialize."""
        self.storage = storage

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        self.storage.add(file)

    def commit(self) -> None:
        """Commit all stores."""
        self.storage.commit()

    def rollback(self) -> None:
        """Rollback all stores."""
        self.storage.rollback()
