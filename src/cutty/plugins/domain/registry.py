"""Hook registry."""
import abc
from collections.abc import Callable
from typing import Any
from typing import overload

from cutty.plugins.domain.hooks import F
from cutty.plugins.domain.hooks import FirstResultHook
from cutty.plugins.domain.hooks import Hook
from cutty.plugins.domain.hooks import R


class Registry(abc.ABC):
    """A registry for hook implementations."""

    @overload
    def bind(self, __hook: FirstResultHook[F]) -> F:
        ...

    @overload
    def bind(self, __hook: Hook[Callable[..., R]]) -> Callable[..., list[R]]:
        ...

    @abc.abstractmethod
    def bind(self, hook: Hook[Any]) -> Callable[..., Any]:
        """Return a callable that dispatches to hook implementations."""

    @abc.abstractmethod
    def register(self, implementation: F) -> None:
        """Register the hook implementation."""
