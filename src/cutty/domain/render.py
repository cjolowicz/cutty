"""Rendering."""
import functools
from collections.abc import Callable
from collections.abc import Sequence
from typing import get_type_hints
from typing import Optional
from typing import overload
from typing import TypeVar
from typing import Union

from cutty.domain.files import Buffer
from cutty.domain.variables import Value
from cutty.domain.variables import Variable
from cutty.domain.varspecs import VariableSpecification
from cutty.filesystem.pure import PurePath


T = TypeVar("T")
U = TypeVar("U")
Variables = Sequence[Variable[Value]]
RenderFunction = Callable[[T, Variables, Variables], T]
RenderContinuation = Callable[[T, Variables, Variables, RenderFunction[U]], T]
RenderDecorator = Callable[[RenderContinuation[T, U]], RenderContinuation[T, U]]


class Renderer:
    """Render."""

    def __init__(self) -> None:
        """Initialize."""

        @functools.singledispatch
        def _render(value: T, variables: Variables, settings: Variables) -> T:
            return value

        self._render = _render

    def __call__(self, value: T, variables: Variables, settings: Variables) -> T:
        """Render."""
        return self._render(value, variables, settings)

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
        def _(value: T, variables: Variables, settings: Variables) -> T:
            assert function is not None  # noqa: S101
            return function(value, variables, settings, self)

        return function

    @classmethod
    def create(cls) -> Renderer:
        """Create a renderer with the default behavior."""
        render = cls()

        @render.register(list)
        def _(
            values: list[T],
            variables: Variables,
            settings: Variables,
            render: RenderFunction[T],
        ) -> list[T]:
            return [render(value, variables, settings) for value in values]

        @render.register(dict)  # type: ignore[no-redef]
        def _(
            mapping: dict[str, T],
            variables: Variables,
            settings: Variables,
            render: RenderFunction[T],
        ) -> dict[str, T]:
            return {
                render(key, variables, settings): render(value, variables, settings)
                for key, value in mapping.items()
            }

        @render.register(VariableSpecification)  # type: ignore[no-redef]
        def _(
            specification: VariableSpecification[Value],
            variables: Variables,
            settings: Variables,
            render: RenderFunction[T],
        ) -> VariableSpecification[Value]:
            return VariableSpecification(
                specification.name,
                specification.description,
                specification.type,
                render(specification.default, variables, settings),
                tuple(
                    render(choice, variables, settings)
                    for choice in specification.choices
                ),
                specification.interactive,
            )

        @render.register  # type: ignore[no-redef]
        def _(
            path: PurePath,
            variables: Variables,
            settings: Variables,
            render: RenderFunction[T],
        ) -> PurePath:
            return PurePath(*(render(part, variables, settings) for part in path.parts))

        @render.register  # type: ignore[no-redef]
        def _(
            buffer: Buffer,
            variables: Variables,
            settings: Variables,
            render: RenderFunction[T],
        ) -> Buffer:
            return Buffer(
                render(buffer.path, variables, settings),
                buffer.mode,
                render(buffer.read(), variables, settings),
            )

        return render
