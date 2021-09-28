"""Creating projects from templates."""
from collections.abc import Callable
from pathlib import Path

from cutty.repositories.domain.repository import Repository as Template


CreateProject = Callable[[Path], Template]
