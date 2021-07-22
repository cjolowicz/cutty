"""Rendering Cookiecutter templates."""
import fnmatch
from collections.abc import Sequence
from typing import Any

from binaryornot.helpers import is_binary_string

from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.cookiecutter.extensions import DEFAULT_EXTENSIONS
from cutty.templates.adapters.jinja import createjinjarenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import asrendercontinuation
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.render import RenderRegistry


def is_binary(blob: bytes) -> bool:
    """Return True if the blob contains binary data."""
    result: bool = is_binary_string(blob[:1024])
    return result


def asstringlist(settings: dict[str, Any], name: str) -> list[str]:
    """Return a setting as a list of strings."""
    value = settings.get(name, [])
    assert isinstance(value, list) and all(  # noqa: S101
        isinstance(item, str) for item in value
    )
    return value


# Avoid generic render functions for lists and dicts.
# https://github.com/agronholm/typeguard/issues/196


def renderlist(
    values: list[Any], bindings: Sequence[Binding], render: Renderer
) -> list[Any]:
    """Render a list."""
    return [render(value, bindings) for value in values]


def renderdict(
    mapping: dict[str, Any], bindings: Sequence[Binding], render: Renderer
) -> dict[str, Any]:
    """Render a dictionary."""
    return {
        render(key, bindings): render(value, bindings) for key, value in mapping.items()
    }


def registerrenderers(path: Path, config: Config) -> RenderRegistry:  # noqa: C901
    """Register render functions."""
    copy_without_render = asstringlist(config.settings, "_copy_without_render")
    extensions = DEFAULT_EXTENSIONS[:]
    extensions.extend(asstringlist(config.settings, "_extensions"))

    def renderregularfile(
        file: RegularFile, bindings: Sequence[Binding], render: Renderer
    ) -> RegularFile:
        """Render a file."""
        cls = Executable if isinstance(file, Executable) else RegularFile
        path = render(file.path, bindings)

        ancestors = [file.path, *file.path.parents[:-1]]
        for ancestor in reversed(ancestors):
            for pattern in copy_without_render:
                if fnmatch.fnmatch(str(ancestor), pattern):
                    return cls(path, file.blob)

        if is_binary(file.blob):
            return cls(path, file.blob)

        text = file.blob.decode()
        text = render(text, bindings)
        return cls(path, text.encode())

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
        RegularFile: renderregularfile,
    }


def createcookiecutterrenderer(path: Path, config: Config) -> Renderer:
    """Create Cookiecutter renderer."""
    renderregistry = registerrenderers(path, config)
    return createrenderer({**defaultrenderregistry, **renderregistry})
