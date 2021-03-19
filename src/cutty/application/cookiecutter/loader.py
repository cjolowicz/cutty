"""Cookiecutter loader."""
import json
from collections.abc import Iterator
from typing import Any

from cutty.adapters.jinja.renderables import JinjaRenderableLoader
from cutty.domain.files import Buffer
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.loader import FileLoader
from cutty.domain.loader import RenderableLoaderFactory
from cutty.domain.loader import VariableSpecificationLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType
from cutty.filesystem.base import Access
from cutty.filesystem.path import Path


def walkfiles(path: Path) -> Iterator[Path]:
    """Iterate over the files under the path."""
    if path.is_file():
        yield path
    elif path.is_dir():
        for entry in path.iterdir():
            yield from walkfiles(entry)
    else:  # pragma: no cover
        raise RuntimeError(f"{path}: not a regular file or directory")


class CookiecutterFileLoader(FileLoader):
    """A loader for project files in a Cookiecutter template."""

    def load(self, path: Path) -> Iterator[File]:
        """Load project files."""
        for template_dir in path.iterdir():
            if all(
                token in template_dir.name for token in ("{{", "cookiecutter", "}}")
            ):
                break
        else:
            raise RuntimeError("template directory not found")  # pragma: no cover

        for path in walkfiles(template_dir):
            blob = path.read_text()
            mode = Mode.EXECUTABLE if path.access(Access.EXECUTE) else Mode.DEFAULT
            yield Buffer(path, mode, blob)


def get_variable_type(value: Any) -> VariableType:
    """Return the appropriate variable type for the value."""
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


def loadvalue(value: Any) -> Value:
    """Stringize scalars except None."""
    if isinstance(value, (bool, int, float)):
        return str(value)

    if isinstance(value, (type(None), str, list, dict)):
        return value

    raise RuntimeError(f"unsupported variable type {type(value)}")  # pragma: no cover


def loadvariable(name: str, value: Value) -> VariableSpecification[Value]:
    """Load a variable specification."""
    interactive = not name.startswith("_")
    # FIXME: Do not render variables with a leading underscore.

    if interactive and isinstance(value, list):
        [variable_type] = set(get_variable_type(choice) for choice in value)
        return VariableSpecification(
            name=name,
            description=name,
            type=variable_type,
            default=value[0],
            choices=tuple(value),
            interactive=interactive,
        )

    return VariableSpecification(
        name=name,
        description=name,
        type=get_variable_type(value),
        default=value,
        choices=(),
        interactive=interactive,
    )


class CookiecutterVariableSpecificationLoader(VariableSpecificationLoader):
    """Loading variable specifications for a Cookiecutter template."""

    def load(self, path: Path) -> Iterator[VariableSpecification[Value]]:
        """Load variable specifications."""
        text = (path / "cookiecutter.json").read_text()
        data = json.loads(text)

        assert isinstance(data, dict) and all(  # noqa: S101
            isinstance(name, str) for name in data
        )

        for name, value in data.items():
            value = loadvalue(value)
            yield loadvariable(name, value)


class CookiecutterRenderableLoaderFactory(RenderableLoaderFactory):
    """Creating a renderable loader."""

    def create(self, path: Path) -> RenderableLoader[str]:
        """Create renderable loader."""
        text = (path / "cookiecutter.json").read_text()
        data = json.loads(text)

        assert isinstance(data, dict) and all(  # noqa: S101
            isinstance(name, str) for name in data
        )

        extensions = data.get("_extensions", [])

        assert isinstance(extensions, list) and all(  # noqa: S101
            isinstance(item, str) for item in extensions
        )

        return JinjaRenderableLoader.create(
            searchpath=[path],
            context_prefix="cookiecutter",
            extra_extensions=extensions,
        )
