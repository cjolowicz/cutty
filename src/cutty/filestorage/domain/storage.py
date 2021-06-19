"""File storage abstraction."""
from __future__ import annotations

import abc
from types import TracebackType
from typing import Optional

from cutty.filestorage.domain.files import File


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

    def __enter__(self) -> FileStorage:
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
