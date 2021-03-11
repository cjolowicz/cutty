"""Loading Cookiecutter templates."""
import json
import pathlib

from cutty.adapters.filesystem.files import loadbuffers
from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.application.cookiecutter import variables
from cutty.domain.files import loadfiles
from cutty.domain.files import RenderableFileLoader
from cutty.domain.templates import Template


def find_template_dir(root: pathlib.Path) -> pathlib.Path:
    """Find the directory where the template is located."""
    for path in root.iterdir():
        if all(token in path.name for token in ("{{", "cookiecutter", "}}")):
            return path
    raise RuntimeError("template directory not found")  # pragma: no cover


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

    template_dir = find_template_dir(path)
    files = loadbuffers(template_dir, relative_to=path)
    hooks = loadbuffers(path / "hooks", relative_to=path)  # TODO: filter
    loader = JinjaRenderableLoader.create(
        searchpath=[template_dir],
        context_prefix="cookiecutter",
        extra_extensions=extensions,
    )
    fileloader = RenderableFileLoader(loader)

    return Template(
        variables=variables.load(loader, data),
        files=loadfiles(files, fileloader),
        hooks=loadfiles(hooks, fileloader),
    )
