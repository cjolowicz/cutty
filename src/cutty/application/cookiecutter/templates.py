"""Loading Cookiecutter templates."""
import json
import pathlib
from collections.abc import Iterator

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.application.cookiecutter import variables
from cutty.domain.paths import Path
from cutty.domain.templates import Template


def _walk_files(path: pathlib.Path) -> Iterator[pathlib.Path]:
    for entry in path.iterdir():
        if entry.is_dir():
            yield from _walk_files(entry)
        elif entry.is_file():
            yield entry
        else:  # pragma: no cover
            raise RuntimeError(f"{entry} is neither regular file nor directory")


def _load_paths(repository: pathlib.Path) -> Iterator[Path]:
    for path in _walk_files(repository):
        path = path.relative_to(repository)
        root = path.parts[0]
        if all(token in root for token in ("{{", "cookiecutter", "}}")):
            yield Path.fromparts(path.parts)


def load(path: pathlib.Path) -> Template:
    """Load a Cookiecutter template."""
    with (path / "cookiecutter.json").open() as io:
        data = json.load(io)
    assert isinstance(data, dict) and all(  # noqa: S101
        isinstance(name, str) for name in data
    )
    extensions = data.get("_extensions", [])
    assert isinstance(extensions, list) and all(  # noqa: S101
        isinstance(item, str) for item in extensions
    )
    loader = JinjaRenderableLoader.create(
        path, context_prefix="cookiecutter", extra_extensions=extensions
    )
    paths = _load_paths(path)
    return Template(
        loader=loader,
        variables=variables.load(loader, data),
        paths=paths,
    )
