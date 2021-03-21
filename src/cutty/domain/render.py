"""Rendering."""
import functools
from collections.abc import Callable
from collections.abc import Sequence
from typing import get_type_hints
from typing import Optional
from typing import overload
from typing import TypeVar
from typing import Union

from cutty.domain.bindings import Binding
from cutty.domain.bindings import Value
from cutty.domain.files import Buffer
from cutty.domain.variables import Variable
from cutty.filesystem.pure import PurePath


T = TypeVar("T")
U = TypeVar("U")
Bindings = Sequence[Binding[Value]]
RenderFunction = Callable[[T, Bindings, Bindings], T]
RenderContinuation = Callable[[T, Bindings, Bindings, RenderFunction[U]], T]
RenderDecorator = Callable[[RenderContinuation[T, U]], RenderContinuation[T, U]]


class Renderer:
    """Render."""

    def __init__(self) -> None:
        """Initialize."""

        @functools.singledispatch
        def _render(value: T, bindings: Bindings, settings: Bindings) -> T:
            return value

        self._render = _render

    def __call__(self, value: T, bindings: Bindings, settings: Bindings) -> T:
        """Render."""
        return self._render(value, bindings, settings)

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
        def _(value: T, bindings: Bindings, settings: Bindings) -> T:
            assert function is not None  # noqa: S101
            return function(value, bindings, settings, self)

        return function

    @classmethod
    def create(cls) -> Renderer:
        """Create a renderer with the default behavior."""
        render = cls()

        @render.register(list)
        def _(
            values: list[T],
            bindings: Bindings,
            settings: Bindings,
            render: RenderFunction[T],
        ) -> list[T]:
            return [render(value, bindings, settings) for value in values]

        @render.register(dict)  # type: ignore[no-redef]
        def _(
            mapping: dict[str, T],
            bindings: Bindings,
            settings: Bindings,
            render: RenderFunction[T],
        ) -> dict[str, T]:
            return {
                render(key, bindings, settings): render(value, bindings, settings)
                for key, value in mapping.items()
            }

        @render.register(Variable)  # type: ignore[no-redef]
        def _(
            variable: Variable[Value],
            bindings: Bindings,
            settings: Bindings,
            render: RenderFunction[T],
        ) -> Variable[Value]:
            return Variable(
                variable.name,
                variable.description,
                variable.type,
                render(variable.default, bindings, settings),
                tuple(
                    render(choice, bindings, settings) for choice in variable.choices
                ),
                variable.interactive,
            )

        @render.register  # type: ignore[no-redef]
        def _(
            path: PurePath,
            bindings: Bindings,
            settings: Bindings,
            render: RenderFunction[T],
        ) -> PurePath:
            return PurePath(*(render(part, bindings, settings) for part in path.parts))

        @render.register  # type: ignore[no-redef]
        def _(
            buffer: Buffer,
            bindings: Bindings,
            settings: Bindings,
            render: RenderFunction[T],
        ) -> Buffer:
            return Buffer(
                render(buffer.path, bindings, settings),
                buffer.mode,
                render(buffer.read(), bindings, settings),
            )

        return render
