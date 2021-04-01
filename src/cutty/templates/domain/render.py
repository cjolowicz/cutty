"""Rendering."""
from __future__ import annotations

import functools
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import get_type_hints
from typing import Optional
from typing import overload
from typing import TypeVar
from typing import Union

from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.files import File
from cutty.templates.domain.variables import GenericVariable
from cutty.templates.domain.variables import Variable


T = TypeVar("T")
U = TypeVar("U")

GenericRenderFunction = Callable[[T, Sequence[Binding]], T]
RenderFunction = GenericRenderFunction[Any]
RenderContinuation = Callable[[T, Sequence[Binding], GenericRenderFunction[U]], T]
RenderDecorator = Callable[[RenderContinuation[T, U]], RenderContinuation[T, U]]


# Use RenderFunction for the third argument instead of GenericRenderFunction[T],
# because passing a generic render function does not work with mypy.
# https://github.com/python/mypy/issues/1317


def rendervariable(
    variable: Variable,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> Variable:
    """Render a variable."""
    return Variable(
        variable.name,
        variable.description,
        variable.type,
        render(variable.default, bindings),
        tuple(render(choice, bindings) for choice in variable.choices),
        variable.interactive,
    )


def renderpath(
    path: PurePath,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> PurePath:
    """Render a path."""
    return PurePath(*(render(part, bindings) for part in path.parts))


def renderfile(
    file: File,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> File:
    """Render a file."""
    return File(
        render(file.path, bindings),
        file.mode,
        render(file.blob, bindings),
    )


class Renderer:
    """Render."""

    def __init__(self) -> None:
        """Initialize."""

        @functools.singledispatch
        def _render(value: T, bindings: Sequence[Binding]) -> T:
            return value

        self._render = _render

    def __call__(self, value: T, bindings: Sequence[Binding]) -> T:
        """Render."""
        return self._render(value, bindings)

    @overload
    def register(
        self, __function: RenderContinuation[T, U]
    ) -> RenderContinuation[T, U]:
        """Overload for use as ``@render.register``."""

    @overload
    def register(self, __cls: type[T]) -> RenderDecorator[T, U]:
        """Overload for use as ``@render.register(cls)``."""  # noqa: D402

    @overload
    def register(
        self, __cls: type[T], __function: RenderContinuation[T, U]
    ) -> RenderContinuation[T, U]:
        """Overload for use as ``render.register(cls, function)``."""  # noqa: D402

    def register(
        self,
        cls: Union[type[T], RenderContinuation[T, U]],
        function: Optional[RenderContinuation[T, U]] = None,
    ) -> Union[RenderContinuation[T, U], RenderDecorator[T, U]]:
        """Register a render continuation function."""
        if function is None:
            if isinstance(cls, type):
                return lambda function: self.register(cls, function)

            function, cls = cls, next(
                hint for key, hint in get_type_hints(cls).items() if key != "return"
            )

        @self._render.register(cls)
        def _(value: T, bindings: Sequence[Binding]) -> T:
            assert function is not None  # noqa: S101
            return function(value, bindings, self)

        return function

    @classmethod
    def create(cls) -> Renderer:
        """Create a renderer with the default behavior."""
        render = cls()

        render.register(GenericVariable, rendervariable)
        render.register(PurePath, renderpath)
        render.register(File, renderfile)

        return render
