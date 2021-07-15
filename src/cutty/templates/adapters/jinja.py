"""Rendering with Jinja."""
from __future__ import annotations

import contextlib
from collections.abc import Callable
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Union

import jinja2

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import GenericRenderer
from cutty.util.reraise import reraise


@dataclass
class TemplateExtensionNotFoundError(Exception):
    """The template extension was not found."""

    extension: str


@dataclass
class TemplateExtensionTypeError(Exception):
    """The template extension does not have the expected type."""

    extension: str
    type: str


def import_object(import_path: str) -> Any:
    """Import the object at the given import path.

    Import paths consist of the dotted module name, optionally followed by a
    colon or dot, and the module attribute at which the object is located.

    For example:

    - ``json``
    - ``os.path``
    - ``xml.sax.saxutils:escape``
    - ``xml.sax.saxutils.escape``

    This function mirrors the implementation of ``jinja2.utils.import_string``.
    """
    if ":" in import_path:
        module_name, _, attribute = import_path.rpartition(":")
    elif "." in import_path:
        module_name, _, attribute = import_path.rpartition(".")
    else:
        return __import__(import_path)

    module = __import__(module_name, None, None, [attribute])
    return getattr(module, attribute)


def load_extension(import_path: str) -> type[jinja2.ext.Extension]:
    """Import a Jinja extension from the specified path."""
    with reraise(TemplateExtensionNotFoundError(import_path)):
        extension = import_object(import_path)

    if not (
        isinstance(extension, type) and issubclass(extension, jinja2.ext.Extension)
    ):
        raise TemplateExtensionTypeError(import_path, str(type(extension)))

    return extension


def splitpath(pathstr: str) -> tuple[str, ...]:
    """Split a path into segments and perform a sanity check.

    If it detects '..' in the path it will raise a `TemplateNotFound` error.

    source: jinja2.loaders.split_template_path
    """
    # TODO: Add string parsing to PurePath?
    # TODO: Add common validation function?
    # (see cutty.templates.domain.render.renderfiles)
    import os

    parts = tuple(part for part in pathstr.split("/") if part and part != os.curdir)

    if any(
        any(sep in part for sep in (os.sep, os.altsep) if sep) or part == os.pardir
        for part in parts
    ):
        raise jinja2.TemplateNotFound(pathstr)

    return parts


class _FilesystemLoader(jinja2.BaseLoader):
    """Load templates from a directory in the file system."""

    def __init__(self, *, searchpath: Iterable[Path]):
        """Initialize."""
        self.searchpath = tuple(searchpath)

    def get_source(
        self, environment: jinja2.Environment, template: str
    ) -> tuple[str, str, Callable[[], bool]]:
        """Get the template source, filename and reload helper for a template."""
        parts = splitpath(template)
        for searchpath in self.searchpath:
            path = searchpath.joinpath(*parts)
            with contextlib.suppress(FileNotFoundError):
                return path.read_text(), str(path), lambda: True

        raise jinja2.TemplateNotFound(template)


def createjinjarenderer(
    *,
    searchpath: Iterable[Path],
    context_prefix: Optional[str] = None,
    extra_context: Optional[dict[str, Any]] = None,
    extensions: Iterable[Union[str, type[jinja2.ext.Extension]]] = (),
) -> GenericRenderer[str]:
    """Create a renderer using Jinja."""
    extensions = [
        load_extension(extension) if isinstance(extension, str) else extension
        for extension in extensions
    ]

    environment = jinja2.Environment(  # noqa: S701
        loader=_FilesystemLoader(searchpath=searchpath),
        extensions=extensions,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )

    def rendertext(text: str, bindings: Iterable[Binding]) -> str:
        """Render the text using Jinja."""
        template = environment.from_string(text)
        context = {binding.name: binding.value for binding in bindings}

        if extra_context is not None:
            context.update(extra_context)

        if context_prefix is not None:
            context = {context_prefix: context}

        return template.render(context)

    return rendertext
