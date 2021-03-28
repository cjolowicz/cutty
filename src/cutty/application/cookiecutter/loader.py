"""Cookiecutter loader."""
import fnmatch
import json
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any

from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.jinja.render import JinjaRenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.render import RenderFunction
from cutty.templates.domain.values import getvaluetype
from cutty.templates.domain.values import Value
from cutty.templates.domain.values import ValueType
from cutty.templates.domain.variables import Variable


def loadvalue(value: Any) -> Value:
    """Stringize scalars."""
    if isinstance(value, (bool, int, float)):
        return str(value)

    if isinstance(value, (str, list, dict)):
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

    valuetype = ValueType.STRING if value is None else getvaluetype(value)
    return Variable(
        name=name,
        description=name,
        type=valuetype,
        default=value,
        choices=(),
        interactive=True,
    )


def loadconfig(template: str, path: Path) -> Config:
    """Load the configurations for a Cookiecutter template."""
    text = (path / "cookiecutter.json").read_text()
    data = json.loads(text)

    assert isinstance(data, dict) and all(  # noqa: S101
        isinstance(name, str) for name in data
    )

    data.setdefault("_template", template)

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
            return iter([*loadhooks(path), template_dir])
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover


def loadhooks(path: Path) -> Iterator[Path]:
    """Load hooks in a Cookiecutter template."""
    hookdir = path / "hooks"
    hooks = {"pre_gen_project", "post_gen_project"}

    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~") and path.stem in hooks:
                yield path


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
