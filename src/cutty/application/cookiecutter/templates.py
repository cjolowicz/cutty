"""Loading Cookiecutter templates."""
import json
import pathlib
from collections.abc import Iterator

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.application.cookiecutter import variables
from cutty.domain.files import DefaultRenderableFileRepository
from cutty.domain.paths import Path
from cutty.domain.templates import Template


class CookiecutterRenderableLoader(JinjaRenderableLoader):
    """Cookiecutter-flavored Jinja loader."""

    def list(self) -> Iterator[Path]:
        """Iterate over the paths where renderables are located."""
        for path in super().list():
            root = path.parts[0]
            if all(token in root for token in ("{{", "cookiecutter", "}}")):
                yield path


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
    loader = CookiecutterRenderableLoader.create(
        path, context_prefix="cookiecutter", extra_extensions=extensions
    )
    repository = DefaultRenderableFileRepository(loader, loader)
    return Template(files=repository, variables=variables.load(loader, data))
