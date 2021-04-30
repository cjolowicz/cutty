"""Paths in Cookiecutter templates."""
from collections.abc import Iterator

from cutty.filesystems.domain.path import Path
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry
from cutty.templates.adapters.hooks import getpaths
from cutty.templates.domain.config import Config


def iterhooks(path: Path) -> Iterator[Path]:
    """Load hooks in a Cookiecutter template."""
    hookdir = path / "hooks"
    hooks = {"pre_gen_project", "post_gen_project"}

    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~") and path.stem in hooks:
                yield path


@implements(getpaths)
def getpaths_impl(path: Path, config: Config) -> Iterator[Path]:
    """Iterate over the files and directories to be rendered."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            break
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover

    yield from iterhooks(path)
    yield template_dir


def registerpathiterable(registry: Registry) -> None:
    """Register path iterable."""
    registry.register(getpaths_impl)
