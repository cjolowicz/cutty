"""Rendering with Jinja."""
import contextlib
import itertools
from collections.abc import Callable
from collections.abc import Iterable
from typing import Optional

import jinja2

from cutty.adapters.jinja import extensions
from cutty.domain.bindings import Binding
from cutty.domain.render import RenderFunction
from cutty.domain.render import T
from cutty.filesystem.path import Path


def splitpath(pathstr: str) -> tuple[str, ...]:
    """Split a path into segments and perform a sanity check.

    If it detects '..' in the path it will raise a `TemplateNotFound` error.

    source: jinja2.loaders.split_template_path
    """
    # TODO: Add string parsing to PurePath?
    # TODO: Add common validation function? (see cutty.domain.render.renderfiles)
    import os.path

    separators = [sep for sep in (os.path.sep, os.path.altsep) if sep]
    parts = tuple(part for part in pathstr.split("/") if part and part != ".")

    if any(
        any(sep in part for sep in separators) or part == os.path.pardir
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


class JinjaRenderer:
    """Wrapper for a Jinja environment."""

    @classmethod
    def create(
        cls,
        *,
        searchpath: Iterable[Path],
        context_prefix: Optional[str] = None,
        extra_bindings: Iterable[Binding] = (),
        extra_extensions: Iterable[str] = (),
    ) -> JinjaRenderer:
        """Create a renderer using Jinja."""
        environment = jinja2.Environment(  # noqa: S701
            loader=_FilesystemLoader(searchpath=searchpath),
            extensions=extensions.load(extra=extra_extensions),
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )
        return cls(
            environment,
            context_prefix=context_prefix,
            extra_bindings=extra_bindings,
        )

    def __init__(
        self,
        environment: jinja2.Environment,
        *,
        context_prefix: Optional[str] = None,
        extra_bindings: Iterable[Binding] = (),
    ) -> None:
        """Initialize."""
        self.environment = environment
        self.context_prefix = context_prefix
        self.extra_bindings = tuple(extra_bindings)

    def __call__(
        self, text: str, bindings: Iterable[Binding], render: RenderFunction[T]
    ) -> str:
        """Render the text."""
        template = self.environment.from_string(text)
        context = {
            variable.name: variable.value
            for variable in itertools.chain(self.extra_bindings, bindings)
        }

        if self.context_prefix is not None:
            context = {self.context_prefix: context}

        return template.render(context)
