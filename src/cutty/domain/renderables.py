"""Rendering."""
import abc
from collections.abc import Iterable
from collections.abc import Sequence
from typing import Generic
from typing import TypeVar

from cutty.domain.variables import Value
from cutty.domain.variables import Variable


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Renderable(abc.ABC, Generic[T_co]):
    """Something that can be rendered using variables."""

    @abc.abstractmethod
    def render(self, variables: Sequence[Variable[Value]]) -> T_co:
        """Render the object."""


class RenderableLoader(abc.ABC, Generic[T]):
    """Something that can load renderables."""

    @abc.abstractmethod
    def load(self, value: T) -> Renderable[T]:
        """Load the renderable."""


class TrivialRenderable(Renderable[T_co]):
    """A renderable that just returns its value."""

    def __init__(self, value: T_co) -> None:
        """Initialize."""
        self.value = value

    def render(self, variables: Sequence[Variable[Value]]) -> T_co:
        """Return the value."""
        return self.value


class RenderableList(Renderable[list[Value]]):
    """A renderable list."""

    def __init__(self, renderables: Iterable[Renderable[Value]]) -> None:
        """Initialize."""
        self.renderables = list(renderables)

    def render(self, variables: Sequence[Variable[Value]]) -> list[Value]:
        """Return a list of rendered items."""
        return [renderable.render(variables) for renderable in self.renderables]


class RenderableDict(Renderable[dict[str, Value]]):
    """A renderable dictionary."""

    def __init__(
        self, renderables: Iterable[tuple[Renderable[str], Renderable[Value]]]
    ) -> None:
        """Initialize."""
        self.renderables = list(renderables)

    def render(self, variables: Sequence[Variable[Value]]) -> dict[str, Value]:
        """Return a dictionary of rendered key-value pairs."""
        return {
            key.render(variables): value.render(variables)
            for key, value in self.renderables
        }


class RenderableValueLoader(RenderableLoader[Value]):
    """Load renderable values."""

    def __init__(self, loader: RenderableLoader[str]) -> None:
        """Initialize."""
        self.loader = loader

    def load(self, value: Value) -> Renderable[Value]:
        """Load renderable."""
        if isinstance(value, str):
            return self.loader.load(value)

        if isinstance(value, list):
            return RenderableList(self.load(item) for item in value)

        if isinstance(value, dict):
            assert all(isinstance(key, str) for key in value)  # noqa: S101
            return RenderableDict(
                (self.loader.load(key), self.load(item)) for key, item in value.items()
            )

        return TrivialRenderable(value)
