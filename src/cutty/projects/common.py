"""Common functionality for projects."""
from collections.abc import Callable
from pathlib import Path

from cutty.repositories.domain.repository import Repository as Template


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


CreateProject = Callable[[Path], Template]
