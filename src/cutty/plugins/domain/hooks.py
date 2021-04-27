"""Hooks."""
from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import Literal
from typing import Optional
from typing import overload
from typing import TypeVar


R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


class Hook(Generic[F]):
    """The interface for a hook.

    Hooks can have zero, one, or many implementations.
    """

    def __init__(self, function: F) -> None:
        """Initialize."""
        self.function = function


class FirstResultHook(Hook[F]):
    """Dispatch only until an implementation returns not None."""


@overload
def hook(__function: F) -> Hook[F]:
    ...


@overload
def hook(*, firstresult: Literal[True]) -> Callable[[F], FirstResultHook[F]]:
    ...


@overload
def hook(*, firstresult: bool = False) -> Callable[[F], Hook[F]]:
    ...


@overload
def hook(
    __function: F, *, firstresult: Literal[True]
) -> Callable[[F], FirstResultHook[F]]:
    ...


@overload
def hook(__function: F, *, firstresult: bool) -> Callable[[F], Hook[F]]:
    ...


def hook(
    function: Optional[Callable[..., Any]] = None, *, firstresult: bool = False
) -> Any:
    """Decorator for defining hooks."""
    if function is None:
        return lambda function: hook(function, firstresult=firstresult)

    cls = FirstResultHook if firstresult else Hook
    return cls(function)


def implements(hook: Hook[F]) -> Callable[[F], F]:
    """Decorator factory for implementing hooks."""

    def decorator(function: F) -> F:
        """Decorator for the hook implementation."""
        function._hook = hook  # type: ignore[attr-defined]
        return function

    return decorator
