"""Rendering Cookiecutter templates."""
import fnmatch
from collections.abc import Sequence
from typing import Any

from cutty.application.cookiecutter.extensions import DEFAULT_EXTENSIONS
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.jinja import createrenderer
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.files import File
from cutty.templates.domain.render import GenericRenderFunction
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.render import RenderFunction
from cutty.templates.domain.render import T


def asstringlist(settings: dict[str, Any], name: str) -> list[str]:
    """Return a setting as a list of strings."""
    value = settings.get(name, [])
    assert isinstance(value, list) and all(  # noqa: S101
        isinstance(item, str) for item in value
    )
    return value


def loadrenderer(path: Path, config: Config) -> Renderer:
    """Create renderer."""
    copy_without_render = asstringlist(config.settings, "_copy_without_render")
    extensions = DEFAULT_EXTENSIONS[:]
    extensions.extend(asstringlist(config.settings, "_extensions"))

    jinja = createrenderer(
        searchpath=[path],
        context_prefix="cookiecutter",
        extra_context=config.settings,
        extensions=extensions,
    )

    render = Renderer.create()
    render.register(str, jinja)

    @render.register(list)
    def _(
        values: list[T], bindings: Sequence[Binding], render: GenericRenderFunction[T]
    ) -> list[T]:
        return [render(value, bindings) for value in values]

    @render.register(dict)  # type: ignore[no-redef]
    def _(
        mapping: dict[str, T],
        bindings: Sequence[Binding],
        render: GenericRenderFunction[T],
    ) -> dict[str, T]:
        return {
            render(key, bindings): render(value, bindings)
            for key, value in mapping.items()
        }

    @render.register(File)  # type: ignore[no-redef]
    def _(file: File, bindings: Sequence[Binding], render: RenderFunction) -> File:
        path = render(file.path, bindings)

        if any(
            fnmatch.fnmatch(str(file.path), pattern) for pattern in copy_without_render
        ):
            return File(path, file.mode, file.blob)

        return File(path, file.mode, render(file.blob, bindings))

    return render
