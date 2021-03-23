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
from cutty.domain.hooks import Hook
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.domain.render import Renderer
from cutty.domain.render import RenderFunction
from cutty.domain.values import getvaluetype
from cutty.domain.values import Value
from cutty.domain.variables import Variable
from cutty.filesystem.path import Path


def loadpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            return iter([template_dir])
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover


def loadhooks(path: Path, config: Config) -> Iterator[Hook]:
    """Load hooks in a Cookiecutter template."""
    hookdir = path / "hooks"
    events = {
        "pre_gen_project": PreGenerateProject,
        "post_gen_project": PostGenerateProject,
    }

    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~"):
                for name, event in events.items():
                    if path.stem == name:
                        yield Hook(path, event)


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


def loadrenderer(path: Path, config: Config) -> Renderer:
    """Create renderer."""
    for setting in config.settings:
        if setting.name == "_extensions":
            extensions = setting.value
            break
    else:
        extensions = []

    assert isinstance(extensions, list) and all(  # noqa: S101
        isinstance(item, str) for item in extensions
    )

    for setting in config.settings:
        if setting.name == "_copy_without_render":
            copy_without_render = setting.value
            break
    else:
        copy_without_render = []

    assert isinstance(copy_without_render, list) and all(  # noqa: S101
        isinstance(item, str) for item in copy_without_render
    )

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
            fnmatch.fnmatch(pattern, str(file.path))
            for pattern in copy_without_render  # type: ignore[union-attr]
        ):
            return File(path, file.mode, file.blob)

        return File(path, file.mode, render(file.blob, bindings))

    return render
