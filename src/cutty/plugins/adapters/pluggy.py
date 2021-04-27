"""Pluggy-based registry."""
import inspect
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from typing import overload

import pluggy

from cutty.plugins.domain.hooks import F
from cutty.plugins.domain.hooks import FirstResultHook
from cutty.plugins.domain.hooks import Hook
from cutty.plugins.domain.hooks import R
from cutty.plugins.domain.registry import Registry


class _Namespace(SimpleNamespace):
    def __hash__(self) -> int:
        """Return a hash value for this instance."""
        return id(self)


class PluggyRegistry(Registry):
    """A registry implementation based on pluggy."""

    def __init__(self, projectname: str = "") -> None:
        """Initialize."""
        self.manager = pluggy.PluginManager(projectname)
        self.hookspec = pluggy.HookspecMarker(projectname)
        self.hookimpl = pluggy.HookimplMarker(projectname)

    @overload
    def bind(self, __hook: FirstResultHook[F]) -> F:
        ...

    @overload
    def bind(self, __hook: Hook[Callable[..., R]]) -> Callable[..., list[R]]:
        ...

    def bind(self, hook: Hook[Any]) -> Callable[..., Any]:
        """Return a callable that dispatches to hook implementations."""
        signature = inspect.signature(hook.function)
        hookname = hook.function.__name__
        hookspec = self.hookspec(
            hook.function, firstresult=isinstance(hook, FirstResultHook)
        )
        namespace = _Namespace()
        setattr(namespace, hookname, hookspec)
        self.manager.add_hookspecs(namespace)

        def dispatch(*args: Any, **kwargs: Any) -> Any:
            """Dispatch to the hook implementations."""
            boundargs = signature.bind(*args, **kwargs)
            dispatcher = getattr(self.manager.hook, hookname)
            return dispatcher(**boundargs.arguments)

        return dispatch

    def register(self, implementation: F) -> None:
        """Register the hook implementation."""
        hook = implementation._hook  # type: ignore[attr-defined]
        hookname = hook.function.__name__
        hookimpl = self.hookimpl(implementation)
        namespace = _Namespace()
        setattr(namespace, hookname, hookimpl)
        self.manager.register(namespace)
