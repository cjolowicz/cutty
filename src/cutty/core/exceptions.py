"""Exceptions."""
from typing import Any
from typing import Iterator
from typing import Optional
from typing import Type

from .compat import contextmanager


class CuttyException(Exception):
    """Base class for cutty exceptions."""

    def __str__(self) -> str:
        """Convert the exception to a string."""
        assert self.__doc__ is not None  # noqa: S101
        message = self.__doc__.format(*self.args)
        if self.__cause__ is not None:
            message = message.rstrip(".")
            message = f"{message}: {self.__cause__}"
        return message

    def __enter__(self) -> None:
        """Enter the context."""

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        """Exit the context."""
        if isinstance(exception, Exception) and not isinstance(
            exception, CuttyException
        ):
            raise self from exception

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


class ConfigurationFileError(CuttyException):
    """Cannot read configuration file {}."""


class ConfigurationDoesNotExist(CuttyException):
    """Configuration file {} not found."""


class InvalidConfiguration(CuttyException):
    """The configuration file {} is not valid."""


class InvalidAbbreviation(CuttyException):
    """Invalid abbreviation {!r} in {!r}: {!r}."""


class CloneError(CuttyException):
    """Cannot download template from {}."""


class UpdateError(CuttyException):
    """Cannot fetch template updates from {}."""


class InvalidRevision(CuttyException):
    """Invalid template revision {!r}."""


class TemplateDirectoryNotFound(CuttyException):
    """Template directory not found in {}."""


class TemplateConfigurationFileError(CuttyException):
    """Cannot read template configuration file {}."""


class TemplateConfigurationDoesNotExist(CuttyException):
    """Template configuration file {} not found."""


class InvalidTemplateConfiguration(CuttyException):
    """The template configuration file {} is not valid."""


class TemplateConfigurationTypeError(CuttyException):
    """The template configuration file {} is not valid: expected {}, but was {}."""


class MissingTemplateVariable(CuttyException):
    """Missing template variable {} in {}."""


class InvalidTemplateVariable(CuttyException):
    """Invalid template variable {} in {}: expected {}, but was {}."""


class TemplateExtensionNotFound(CuttyException):
    """Template extension {} not found."""


class TemplateExtensionTypeError(CuttyException):
    """Template extension {} is not an instance of jinja2.ext.Extension: {}."""


class RenderError(CuttyException):
    """Cannot render template."""


class VariableRenderError(RenderError):
    """Cannot render template variable {}."""


class PathRenderError(RenderError):
    """Cannot render template path {}."""


class ContentRenderError(RenderError):
    """Cannot render template {}."""


class SymlinkRenderError(RenderError):
    """Cannot render symlink {}: {}."""


class ProjectDirectoryExists(CuttyException):
    """Project directory {} already exists."""


class HookFailed(CuttyException):
    """Hook script {} failed."""


class ProjectGenerationFailed(CuttyException):
    """Project generation failed."""


class ProjectUpdateFailed(CuttyException):
    """Project update failed."""
