"""Loading Cookiecutter templates."""
import json
import pathlib
from collections.abc import Iterator
from typing import Any

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.domain.files import RenderableFileLoader
from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


def _get_variable_type(value: Any) -> VariableType:
    mapping = {
        type(None): VariableType.NULL,
        bool: VariableType.BOOLEAN,
        float: VariableType.NUMBER,
        str: VariableType.STRING,
        list: VariableType.ARRAY,
        dict: VariableType.OBJECT,
    }

    for value_type, variable_type in mapping.items():
        if isinstance(value, value_type):
            return variable_type

    raise RuntimeError(f"unsupported variable type {type(value)}")  # pragma: no cover


def _load_variable(
    loader: RenderableLoader, name: str, value: Any
) -> VariableSpecification[Renderable[Value]]:
    variable_type = _get_variable_type(value)

    if isinstance(value, list):
        [variable_type] = set(_get_variable_type(choice) for choice in value)
        choices = tuple(loader.load(choice) for choice in value)
        return VariableSpecification(
            name,
            name,
            variable_type,
            choices[0],
            choices,
            interactive=True,
        )

    return VariableSpecification(
        name,
        name,
        variable_type,
        loader.load(value),
        choices=(),
        interactive=True,
    )


def _load_variables(
    loader: RenderableLoader, data: dict[str, Any]
) -> list[VariableSpecification[Renderable[Value]]]:
    return [_load_variable(loader, name, value) for name, value in data.items()]


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
    variables = _load_variables(loader, data)
    fileloader = RenderableFileLoader(loader)
    paths = _load_paths(path)
    files = fileloader.load(paths)
    return Template(variables=variables, files=files)
