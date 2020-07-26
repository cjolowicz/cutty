"""Types."""
import subprocess  # noqa: S404
from typing import Any
from typing import Mapping
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    CompletedProcess = subprocess.CompletedProcess[str]  # pragma: no cover
else:
    CompletedProcess = subprocess.CompletedProcess

StrMapping = Mapping[str, Any]
