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
        self.marker = pluggy.HookspecMarker(name)

    def bindhook(self, hook: HookT) -> HookT:
        """Bind a hook to the registry."""
        name = hook.__name__
        namespace = SimpleNamespace()
        setattr(namespace, name, self.marker(hook, firstresult=True))
        self.manager.add_hookspecs(namespace)

        @functools.wraps(hook)
        def dispatch(*args: Any, **kwargs: Any) -> Any:
            """Invoke the hook."""
            dispatcher = getattr(self.manager.hook, name)
            return dispatcher(*args, **kwargs)

        return cast(HookT, dispatch)

    def registerplugin(self, module: str) -> AbstractContextManager[object]:
        """Register a plugin."""
        plugin = importlib.import_module(module)

        self.manager.register(plugin)
        self.manager.check_pending()

        unregister = ExitStack()
        unregister.callback(self.manager.unregister, plugin)
        return unregister

    def registerplugins(self, plugins: Iterable[str]) -> AbstractContextManager[object]:
        """Register plugins."""
        with ExitStack() as stack:
            for plugin in plugins:
                context = self.registerplugin(plugin)
                stack.enter_context(context)

            unregister = stack.pop_all()

        return unregister

    def registerentrypoints(self) -> None:
        """Register plugins installed in the environment."""
        if self.manager.load_setuptools_entrypoints("cutty"):
            self.manager.check_pending()  # pragma: no cover
