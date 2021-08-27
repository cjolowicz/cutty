"""Repository."""
from dataclasses import dataclass
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.revisions import Revision


@dataclass
class Repository:
    """A repository."""

    name: str
    path: Path
    revision: Optional[Revision]
