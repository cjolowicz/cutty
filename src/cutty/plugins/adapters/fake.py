"""Fake registry."""
from collections.abc import Callable
from typing import Any
from typing import overload

from cutty.plugins.domain.hooks import F
from cutty.plugins.domain.hooks import FirstResultHook
from cutty.plugins.domain.hooks import Hook
from cutty.plugins.domain.hooks import R
from cutty.plugins.domain.registry import Registry
from cutty.util.typeguard_ignore import typeguard_ignore


class FakeRegistry(Registry):
    """A fake hook registry."""

    def __init__(self) -> None:
        """Initialize."""
        self.implementations: dict[object, list[Callable[..., Any]]] = {}

    @overload
    def bind(self, __hook: FirstResultHook[F]) -> F:
        ...

    @overload
    def bind(self, __hook: Hook[Callable[..., R]]) -> Callable[..., list[R]]:
        ...

    def bind(self, hook: Hook[Any]) -> Callable[..., Any]:
        """Return a callable that dispatches to hook implementations."""

        def dispatch(*args: Any, **kwargs: Any) -> Any:
            """Dispatch to the hook implementations."""
            implementations = self.implementations.get(hook, [])

            if isinstance(hook, FirstResultHook):
                generator = (
                    result
                    for implementation in implementations
                    if (result := implementation(*args, **kwargs)) is not None
                )
                return next(generator, None)

            return [
                implementation(*args, **kwargs) for implementation in implementations
            ]

        return dispatch

    @typeguard_ignore
    def register(self, implementation: F) -> None:
        """Register the hook implementation."""
        hook = implementation._hook  # type: ignore[attr-defined]
        implementations = self.implementations.setdefault(hook, [])
        implementations.insert(0, implementation)
