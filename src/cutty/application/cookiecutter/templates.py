"""Loading Cookiecutter templates."""
import json
import pathlib

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.application.cookiecutter import paths
from cutty.application.cookiecutter import variables
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.templates import Template
from cutty.domain.variables import Value


class CookiecutterRenderableLoader(JinjaRenderableLoader):
    """Cookiecutter-flavored loader for Jinja templates."""

    def loadscalar(self, value: Value) -> Renderable[Value]:
        """Load renderable from scalar."""
        return TrivialRenderable(str(value) if value is not None else None)


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
    return Template(
        loader=loader,
        variables=variables.load(loader, data),
        paths=paths.load(path),
    )
