"""Rendering."""
import functools
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any
from typing import Mapping
from typing import TypeVar

from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.variables import GenericVariable
from cutty.templates.domain.variables import Variable


T = TypeVar("T")

GenericRenderer = Callable[[T, Sequence[Binding]], T]
Renderer = GenericRenderer[Any]
GenericRenderContinuation = Callable[[T, Sequence[Binding], Renderer], T]
RenderContinuation = GenericRenderContinuation[Any]
RenderRegistry = Mapping[type[Any], RenderContinuation]


def bindrendercontinuation(
    rendercontinuation: GenericRenderContinuation[T], render: Renderer
) -> GenericRenderer[T]:
    """Bind the third argument of a render continuation."""

    def _wrapper(value: T, bindings: Sequence[Binding]) -> T:
        value = rendercontinuation(value, bindings, render)
        return value

    return _wrapper


def createrenderer(renderregistry: RenderRegistry) -> Renderer:
    """Create a renderer."""

    @functools.singledispatch
    def _dispatch(value: T, bindings: Sequence[Binding]) -> T:
        raise NotImplementedError(f"no renderer registered for {type(value)}")

    for rendertype, rendercontinuation in renderregistry.items():
        renderfunction = bindrendercontinuation(rendercontinuation, _dispatch)
        _dispatch.register(rendertype, renderfunction)

    return _dispatch


def asrendercontinuation(
    renderfunction: GenericRenderer[T],
) -> GenericRenderContinuation[T]:
    """Return a render continuation that ignores the third argument."""
    # Use Renderer instead of GenericRenderer[U], because passing a
    # generic render function does not work with mypy.
    # https://github.com/python/mypy/issues/1317

    def _wrapper(value: T, bindings: Sequence[Binding], render: Renderer) -> T:
        return renderfunction(value, bindings)

    return _wrapper


def rendervariable(
    variable: Variable,
    bindings: Sequence[Binding],
    render: Renderer,
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


defaultrenderregistry: RenderRegistry = {GenericVariable: rendervariable}
