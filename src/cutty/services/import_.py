"""Import changes from templates into projects."""
from pathlib import Path
from typing import Optional

from cutty.services.update import update


def import_(projectdir: Path, *, revision: Optional[str]) -> None:
    """Import changes from a template into a project."""
    update(
        projectdir,
        extrabindings=(),
        interactive=True,
        revision=revision,
        directory=None,
    )
