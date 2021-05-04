"""File storage abstraction."""
from collections.abc import Callable
from contextlib import AbstractContextManager

from cutty.filestorage.domain.files import File


FileStore = Callable[[File], None]
FileStoreManager = AbstractContextManager[FileStore]
