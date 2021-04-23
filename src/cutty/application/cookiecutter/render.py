"""Rendering Cookiecutter templates."""
import fnmatch
from collections.abc import Sequence
from typing import Any

from binaryornot.helpers import is_binary_string

from cutty.application.cookiecutter.extensions import DEFAULT_EXTENSIONS
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.jinja import createjinjarenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import asrendercontinuation
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.render import RenderRegistry
from cutty.templates.domain.render import T
from cutty.templates.domain.generate import PathMatcher


def asstringlist(settings: dict[str, Any], name: str) -> list[str]:
    """Return a setting as a list of strings."""
    value = settings.get(name, [])
    assert isinstance(value, list) and all(  # noqa: S101
        isinstance(item, str) for item in value
    )
    return value


def renderlist(
    values: list[T], bindings: Sequence[Binding], render: Renderer
) -> list[T]:
    """Render a list."""
    return [render(value, bindings) for value in values]


def renderdict(
    mapping: dict[str, T], bindings: Sequence[Binding], render: Renderer
) -> dict[str, T]:
    """Render a dictionary."""
    return {
        render(key, bindings): render(value, bindings) for key, value in mapping.items()
    }


def iscopyonly(config: Config) -> PathMatcher:
    """Return a matcher checking the ``_copy_without_render`` setting."""
    copy_without_render = asstringlist(config.settings, "_copy_without_render")

    def _match(path: Path) -> bool:
        return any(
            fnmatch.fnmatch(str(path), pattern) for pattern in copy_without_render
        )

    return _match


def isbinary(path: Path) -> bool:
    """Return True if the file is binary."""
    blob = path.read_bytes()
    result: bool = is_binary_string(blob[:1024])
    return result


def registerrenderers(path: Path, config: Config) -> RenderRegistry:
    """Register render functions."""
    extensions = DEFAULT_EXTENSIONS[:]
    extensions.extend(asstringlist(config.settings, "_extensions"))

    rendertext = createjinjarenderer(
        searchpath=[path],
        context_prefix="cookiecutter",
        extra_context=config.settings,
        extensions=extensions,
    )

    return {
        str: asrendercontinuation(rendertext),
        list: renderlist,
        dict: renderdict,
    }
