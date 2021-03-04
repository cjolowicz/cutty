"""Loading Cookiecutter templates."""
import json
import pathlib

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.application.cookiecutter import paths
from cutty.application.cookiecutter import variables
from cutty.domain.files import RenderableFileLoader
from cutty.domain.templates import Template


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
    fileloader = RenderableFileLoader(loader, paths.load(path))
    return Template(files=fileloader, variables=variables.load(loader, data))
