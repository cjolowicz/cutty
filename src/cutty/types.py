"""Types."""
import os
import subprocess  # noqa: S404
from typing import Any
from typing import Mapping
from typing import TYPE_CHECKING
from typing import Union


if TYPE_CHECKING:  # pragma: no cover
    CompletedProcess = subprocess.CompletedProcess[str]
    PathLike = os.PathLike[str]
else:
    CompletedProcess = subprocess.CompletedProcess
    PathLike = os.PathLike

StrMapping = Mapping[str, Any]
StrPath = Union[str, PathLike]
