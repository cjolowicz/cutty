"""Cookiecutter loader."""
import json
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any

from cutty.adapters.jinja.render import JinjaRenderer
from cutty.domain.bindings import Binding
from cutty.domain.files import Buffer
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.loader import FileLoader
from cutty.domain.loader import RendererFactory
from cutty.domain.loader import TemplateConfigLoader
from cutty.domain.render import Renderer
from cutty.domain.templates import TemplateConfig
from cutty.domain.values import getvaluetype
from cutty.domain.values import Value
from cutty.domain.variables import Variable
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


class CookiecutterTemplateConfigLoader(TemplateConfigLoader):
    """Loading Cookiecutter template configurations."""

    def load(self, path: Path) -> TemplateConfig:
        """Load template configuration."""
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

        return TemplateConfig(settings, bindings)


class CookiecutterRendererFactory(RendererFactory):
    """Creating a renderer."""

    def create(self, path: Path, settings: Sequence[Binding]) -> Renderer:
        """Create renderer."""
        for setting in settings:
            if setting.name == "_extensions":
                extensions = setting.value
                break
        else:
            extensions = []

        assert isinstance(extensions, list) and all(  # noqa: S101
            isinstance(item, str) for item in extensions
        )

        jinja = JinjaRenderer.create(
            searchpath=[path],
            context_prefix="cookiecutter",
            extra_bindings=settings,
            extra_extensions=extensions,
        )

        render = Renderer.create()
        render.register(str, jinja)
        return render
