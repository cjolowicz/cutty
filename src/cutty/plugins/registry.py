"""Plugin manager."""
import functools
import importlib
from collections.abc import Callable
from collections.abc import Iterable
from contextlib import AbstractContextManager
from contextlib import ExitStack
from types import SimpleNamespace
from typing import Any
from typing import cast
from typing import TypeVar

import pluggy


HookT = TypeVar("HookT", bound=Callable[..., Any])


class PluginRegistry:
    """Plugin registry."""

    def __init__(self, name: str) -> None:
        """Initialize."""
        self.manager = pluggy.PluginManager(name)
        self.markspec = pluggy.HookspecMarker(name)
        self.markimpl = pluggy.HookimplMarker(name)

    def bind(self, hook: HookT, *, firstresult: bool = False) -> HookT:
        """Bind a hook to the registry."""
        name = hook.__name__
        namespace = SimpleNamespace()
        setattr(namespace, name, self.markspec(hook, firstresult=firstresult))
        self.manager.add_hookspecs(namespace)

        @functools.wraps(hook)
        def dispatch(*args: Any, **kwargs: Any) -> Any:
            """Invoke the hook."""
            dispatcher = getattr(self.manager.hook, name)
            return dispatcher(*args, **kwargs)

        return cast(HookT, dispatch)

    def implement(
        self, implementation: HookT, *, trylast: bool = False
    ) -> AbstractContextManager[object]:
        """Register a hook implementation."""
        name = implementation.__name__
        namespace = SimpleNamespace()
        setattr(namespace, name, self.markimpl(implementation, trylast=trylast))
        self.manager.register(namespace)
        self.manager.check_pending()

        unregister = ExitStack()
        unregister.callback(self.manager.unregister, namespace)
        return unregister
