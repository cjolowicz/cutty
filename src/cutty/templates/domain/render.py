"""Rendering."""
from __future__ import annotations

import functools
import inspect
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import overload
from typing import TypeVar

from cutty.filesystems.domain.path import Path
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
    """Render a variable by rendering its default and choices."""
    return Variable(
        variable.name,
        variable.description,
        variable.type,
        render(variable.default, bindings),
        tuple(render(choice, bindings) for choice in variable.choices),
        variable.interactive,
    )


def renderpurepath(
    path: PurePath,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> PurePath:
    """Render a path by rendering its parts."""
    return PurePath(*(render(part, bindings) for part in path.parts))


def renderpath(
    path: Path,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> Path:
    """Render a path by rendering its parts."""
    return Path(
        *(render(part, bindings) for part in path.parts),
        filesystem=path.filesystem,
    )


def renderfile(
    file: File,
    bindings: Sequence[Binding],
    render: RenderFunction,
) -> File:
    """Render a file by rendering its path and contents."""
    return File(
        render(file.path, bindings),
        file.mode,
        render(file.blob.decode(), bindings).encode(),
    )


class Renderer:
    """Render."""

    def __init__(self) -> None:
        """Initialize."""

        @functools.singledispatch
        def _render(value: T, bindings: Sequence[Binding]) -> T:
            raise NotImplementedError(f"no renderer registered for {type(value)}")

        self._render = _render

    def __call__(self, value: T, bindings: Sequence[Binding]) -> T:
        """Render."""
        return self._render(value, bindings)

    @overload
    def register(self, __cls: type[T]) -> RenderDecorator[T, U]:
        ...

    @overload
    def register(
        self, __cls: type[T], __function: GenericRenderFunction[T]
    ) -> GenericRenderFunction[T]:
        ...

    @overload
    def register(
        self, __cls: type[T], __function: RenderContinuation[T, U]
    ) -> RenderContinuation[T, U]:
        ...

    def register(self, cls, function=None):  # type: ignore[no-untyped-def]
        """Register a render continuation function."""
        if function is None:
            return lambda function: self.register(cls, function)

        if len(inspect.signature(function).parameters) == 2:
            self._render.register(cls, function)
            return function

        def _callback(value: T, bindings: Sequence[Binding]) -> T:
            value = function(value, bindings, self)
            return value

        self._render.register(cls, _callback)

        return function

    @classmethod
    def create(cls) -> Renderer:
        """Create a renderer with the default behavior."""
        render = cls()

        render.register(GenericVariable, rendervariable)
        render.register(PurePath, renderpurepath)
        render.register(Path, renderpath)
        render.register(File, renderfile)

        return render
