"""Paths in Cookiecutter templates."""
from collections.abc import Iterator

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.config import Config


def iterpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            break
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover

    yield template_dir
