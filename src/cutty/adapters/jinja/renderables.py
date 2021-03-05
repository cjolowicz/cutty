"""Rendering with Jinja."""
import pathlib
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Optional

import jinja2

from cutty.adapters.jinja import extensions
from cutty.domain.paths import Path
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import RenderableRepository
from cutty.domain.variables import Value
from cutty.domain.variables import Variable


class JinjaRenderable(Renderable[str]):
    """Wrapper for a Jinja template."""

    def __init__(
        self,
        template: jinja2.Template,
        *,
        context_prefix: Optional[str] = None,
    ) -> None:
        """Initialize."""
        self.template = template
        self.context_prefix = context_prefix

    def render(self, variables: Sequence[Variable[Value]]) -> str:
        """Render the object to a string."""
        context = {variable.name: variable.value for variable in variables}
        if self.context_prefix is not None:
            context = {self.context_prefix: context}
        return self.template.render(context)


class JinjaRenderableLoader(RenderableLoader, RenderableRepository):
    """Wrapper for a Jinja environment."""

    @classmethod
    def create(
        cls,
        directory: pathlib.Path,
        *,
        context_prefix: Optional[str] = None,
        extra_extensions: Iterable[str] = (),
    ) -> JinjaRenderableLoader:
        """Create a renderable loader using Jinja."""
        environment = jinja2.Environment(  # noqa: S701
            loader=jinja2.FileSystemLoader(str(directory)),
            extensions=extensions.load(extra=extra_extensions),
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )
        return cls(environment, context_prefix=context_prefix)

    def __init__(
        self,
        environment: jinja2.Environment,
        *,
        context_prefix: Optional[str] = None,
    ) -> None:
        """Initialize."""
        self.environment = environment
        self.context_prefix = context_prefix

    def loadtext(self, text: str) -> Renderable[str]:
        """Load renderable from text."""
        template = self.environment.from_string(text)
        return JinjaRenderable(template, context_prefix=self.context_prefix)

    def list(self) -> Iterator[Path]:
        """Iterate over the paths where renderables are located."""
        names = (
            self.environment.loader.list_templates()  # type: ignore[no-untyped-call]
        )
        for name in names:
            yield Path(name.split("/"))

    def get(self, path: Path) -> Renderable[str]:
        """Get renderable by path."""
        name = "/".join(path.parts)
        template = self.environment.get_template(name)
        return JinjaRenderable(template, context_prefix=self.context_prefix)
