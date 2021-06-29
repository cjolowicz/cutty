"""File storage abstraction."""
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
