"""All exceptions used in the cutty code base are defined here."""
import jinja2.exceptions

from ..common.exceptions import CuttyException
from ..common.types import Context


class NonTemplatedInputDirException(CuttyException):
    """Exception for when a project's input dir is not templated.

    The name of the input directory should always contain a string that is
    rendered to something else, so that input_dir != output_dir.
    """


class OutputDirExistsException(CuttyException):
    """Exception for existing output directory.

    Raised when the output directory of the project exists already.
    """


class InvalidModeException(CuttyException):
    """Exception for incompatible modes.

    Raised when cutty is called with both `no_input==True` and
    `replay==True` at the same time.
    """


class FailedHookException(CuttyException):
    """Exception for hook failures.

    Raised when a hook script fails.
    """


class UndefinedVariableInTemplate(CuttyException):
    """Exception for out-of-scope variables.

    Raised when a template uses a variable which is not defined in the
    context.
    """

    def __init__(
        self, message: str, error: jinja2.exceptions.UndefinedError, context: Context
    ) -> None:
        """Exception for out-of-scope variables."""
        self.message = message
        self.error = error
        self.context = context

    def __str__(self) -> str:
        """Text representation of UndefinedVariableInTemplate."""
        return (
            "{self.message}. "
            "Error message: {self.error.message}. "
            "Context: {self.context}"
        ).format(**locals())


class UnknownExtension(CuttyException):
    """Exception for un-importable extention.

    Raised when an environment is unable to import a required extension.
    """
