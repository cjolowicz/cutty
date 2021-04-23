"""Plugin manager."""
import importlib
from collections.abc import Iterable
from contextlib import AbstractContextManager
from contextlib import ExitStack
from typing import Any

import pluggy


class PluginRegistry:
    """Plugin registry."""

    def __init__(self) -> None:
        """Initialize."""
        self.manager = pluggy.PluginManager("cutty")

    def registerhooks(self, modules: Iterable[str]) -> None:
        """Register hooks."""
        for module in modules:
            hookspecs = importlib.import_module(module)
            self.manager.add_hookspecs(hookspecs)

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
            self.manager.check_pending()

    @property
    def dispatch(self) -> Any:
        """Return the dispatcher."""
        return self.manager.hook
