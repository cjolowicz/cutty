"""Cookiecutter loader."""
import fnmatch
import json
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any

from cutty.adapters.jinja.render import JinjaRenderer
from cutty.domain.bindings import Binding
from cutty.domain.config import Config
from cutty.domain.files import File
from cutty.domain.render import Renderer
from cutty.domain.render import RenderFunction
from cutty.domain.values import getvaluetype
from cutty.domain.values import Value
from cutty.domain.variables import Variable
from cutty.filesystem.path import Path


def loadvalue(value: Any) -> Value:
    """Stringize scalars except None."""
    if isinstance(value, (bool, int, float)):
        return str(value)

    if isinstance(value, (type(None), str, list, dict)):
        return value

    raise RuntimeError(f"unsupported value type {type(value)}")  # pragma: no cover


def loadvariable(name: str, value: Value) -> Variable:
    """Load a variable."""
    if isinstance(value, list):
        [valuetype] = set(getvaluetype(choice) for choice in value)
        return Variable(
            name=name,
            description=name,
            type=valuetype,
            default=value[0],
            choices=tuple(value),
            interactive=True,
        )

    return Variable(
        name=name,
        description=name,
        type=getvaluetype(value),
        default=value,
        choices=(),
        interactive=True,
    )


def loadconfig(path: Path) -> Config:
    """Load the configurations for a Cookiecutter template."""
    text = (path / "cookiecutter.json").read_text()
    data = json.loads(text)

    assert isinstance(data, dict) and all(  # noqa: S101
        isinstance(name, str) for name in data
    )

    settings = tuple(
        Binding(name, loadvalue(value))
        for name, value in data.items()
        if name.startswith("_")
    )

    bindings = tuple(
        loadvariable(name, loadvalue(value))
        for name, value in data.items()
        if not name.startswith("_")
    )

    return Config(settings, bindings)


def loadpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            return iter([template_dir])
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover


def asstringlist(settings: Sequence[Binding], name: str) -> list[str]:
    """Return a setting as a list of strings."""
    for setting in settings:
        if setting.name == name:
            assert isinstance(setting.value, list) and all(  # noqa: S101
                isinstance(item, str) for item in setting.value
            )
            return setting.value

    return []


def loadrenderer(path: Path, config: Config) -> Renderer:
    """Create renderer."""
    extensions = asstringlist(config.settings, "_extensions")
    copy_without_render = asstringlist(config.settings, "_copy_without_render")
    jinja = JinjaRenderer.create(
        searchpath=[path],
        context_prefix="cookiecutter",
        extra_bindings=config.settings,
        extra_extensions=extensions,
    )

    render = Renderer.create()
    render.register(str, jinja)

    @render.register
    def _(
        file: File,
        bindings: Sequence[Binding],
        render: RenderFunction[Any],
    ) -> File:
        path = render(file.path, bindings)

        if any(
            fnmatch.fnmatch(pattern, str(file.path)) for pattern in copy_without_render
        ):
            return File(path, file.mode, file.blob)

        return File(path, file.mode, render(file.blob, bindings))

    return render
