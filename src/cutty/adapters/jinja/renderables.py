"""Rendering with Jinja."""
import contextlib
import itertools
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Sequence
from typing import Optional

import jinja2

from cutty.adapters.jinja import extensions
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.variables import Value
from cutty.domain.variables import Variable
from cutty.filesystem.path import Path


class JinjaRenderable(Renderable[str]):
    """Wrapper for a Jinja template."""

    def __init__(
        self,
        template: jinja2.Template,
        *,
        context_prefix: Optional[str] = None,
        extra_variables: Iterable[Variable[Value]] = (),
    ) -> None:
        """Initialize."""
        self.template = template
        self.context_prefix = context_prefix
        self.extra_variables = tuple(extra_variables)

    def render(self, variables: Sequence[Variable[Value]]) -> str:
        """Render the object to a string."""
        context = {
            variable.name: variable.value
            for variable in itertools.chain(self.extra_variables, variables)
        }
        if self.context_prefix is not None:
            context = {self.context_prefix: context}
        return self.template.render(context)


def splitpath(pathstr: str) -> tuple[str, ...]:
    """Split a path into segments and perform a sanity check.

    If it detects '..' in the path it will raise a `TemplateNotFound` error.

    source: jinja2.loaders.split_template_path
    """
    # TODO: Add string parsing to PurePath?
    # TODO: Add common validation function? (see also RenderablePath)
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


class JinjaRenderableLoader(RenderableLoader[str]):
    """Wrapper for a Jinja environment."""

    @classmethod
    def create(
        cls,
        *,
        searchpath: Iterable[Path],
        context_prefix: Optional[str] = None,
        extra_variables: Iterable[Variable[Value]] = (),
        extra_extensions: Iterable[str] = (),
    ) -> JinjaRenderableLoader:
        """Create a renderable loader using Jinja."""
        environment = jinja2.Environment(  # noqa: S701
            loader=_FilesystemLoader(searchpath=searchpath),
            extensions=extensions.load(extra=extra_extensions),
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )
        return cls(
            environment,
            context_prefix=context_prefix,
            extra_variables=extra_variables,
        )

    def __init__(
        self,
        environment: jinja2.Environment,
        *,
        context_prefix: Optional[str] = None,
        extra_variables: Iterable[Variable[Value]] = (),
    ) -> None:
        """Initialize."""
        self.environment = environment
        self.context_prefix = context_prefix
        self.extra_variables = tuple(extra_variables)

    def load(self, text: str, path: Optional[Path] = None) -> Renderable[str]:
        """Load renderable from text."""
        template = self.environment.from_string(text)
        return JinjaRenderable(
            template,
            context_prefix=self.context_prefix,
            extra_variables=self.extra_variables,
        )
