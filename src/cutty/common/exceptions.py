"""Exceptions."""
from typing import Iterator
from typing import Type

from .compat import contextmanager


class CuttyException(Exception):
    """Base class for cutty exceptions."""

    def __str__(self) -> str:
        """Convert the exception to a string."""
        assert self.__doc__ is not None  # noqa: S101
        return self.__doc__.format(*self.args, cause=self.__cause__)

    @contextmanager
    def when(self, *exception_types: Type[Exception]) -> Iterator[None]:
        """Context manager handling exceptions by raising self instead."""
        if not exception_types:
            exception_types = (Exception,)

        try:
            yield
        except CuttyException:
            raise
        except exception_types as exception:
            raise self from exception


class ConfigurationError(CuttyException):
    """Configuration file {} cannot be loaded."""


class ConfigurationDoesNotExist(ConfigurationError):
    """Configuration file {} not found."""


class InvalidConfiguration(ConfigurationError):
    """The configuration file {} is not valid."""
