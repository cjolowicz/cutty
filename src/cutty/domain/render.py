"""Rendering."""
import functools
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import get_type_hints
from typing import Optional
from typing import overload
from typing import TypeVar
from typing import Union

from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.files import loadfile
from cutty.domain.files import walkfiles
from cutty.domain.variables import GenericVariable
from cutty.domain.variables import Variable
from cutty.filesystem.path import Path
from cutty.filesystem.pure import PurePath


T = TypeVar("T")
U = TypeVar("U")
RenderFunction = Callable[[T, Sequence[Binding]], T]
RenderContinuation = Callable[[T, Sequence[Binding], RenderFunction[U]], T]
RenderDecorator = Callable[[RenderContinuation[T, U]], RenderContinuation[T, U]]


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


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

        @render.register(list)
        def _(
            values: list[T], bindings: Sequence[Binding], render: RenderFunction[T]
        ) -> list[T]:
            return [render(value, bindings) for value in values]

        @render.register(dict)  # type: ignore[no-redef]
        def _(
            mapping: dict[str, T],
            bindings: Sequence[Binding],
            render: RenderFunction[T],
        ) -> dict[str, T]:
            return {
                render(key, bindings): render(value, bindings)
                for key, value in mapping.items()
            }

        @render.register(GenericVariable)  # type: ignore[no-redef]
        def _(
            variable: Variable,
            bindings: Sequence[Binding],
            render: RenderFunction[T],
        ) -> Variable:
            return Variable(
                variable.name,
                variable.description,
                variable.type,
                render(variable.default, bindings),
                tuple(render(choice, bindings) for choice in variable.choices),
                variable.interactive,
            )

        @render.register  # type: ignore[no-redef]
        def _(
            path: PurePath,
            bindings: Sequence[Binding],
            render: RenderFunction[T],
        ) -> PurePath:
            return PurePath(*(render(part, bindings) for part in path.parts))

        @render.register  # type: ignore[no-redef]
        def _(
            file: File,
            bindings: Sequence[Binding],
            render: RenderFunction[T],
        ) -> File:
            return File(
                render(file.path, bindings),
                file.mode,
                render(file.blob, bindings),
            )

        return render


def renderfiles(
    paths: Iterable[Path], render: Renderer, bindings: Sequence[Binding]
) -> Iterator[File]:
    """Render the files."""
    for path in paths:
        for path in walkfiles(path):
            name = render(path.name, bindings)

            if not name:
                # FIXME: Can we avoid traversing that directory?
                continue

            if "/" in name or "\\" in name or name == "." or name == "..":
                raise InvalidPathComponent(str(path))

            file = loadfile(path)
            yield render(file, bindings)
