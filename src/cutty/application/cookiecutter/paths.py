"""Paths in Cookiecutter templates."""
from collections.abc import Iterator

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.config import Config


def loadhooks(path: Path) -> Iterator[Path]:
    """Load hooks in a Cookiecutter template."""
    hookdir = path / "hooks"
    hooks = {"pre_gen_project", "post_gen_project"}

    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~") and path.stem in hooks:
                yield path


def loadpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            return iter([*loadhooks(path), template_dir])
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover
