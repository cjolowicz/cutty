"""Markers for hook specifications and implementations."""
from collections.abc import Callable
from typing import Any
from typing import TypeVar

from pluggy import HookimplMarker
from pluggy import HookspecMarker


F = TypeVar("F", bound=Callable[..., Any])

_hookspec = HookspecMarker("cutty")
_hookimpl = HookimplMarker("cutty")


def hookspecification(firstresult: bool) -> Callable[[F], F]:
    """Decorator for a hook specification."""
    decorator: Callable[[F], F] = _hookspec(firstresult=firstresult)
    return decorator


def hookimplementation(trylast: bool) -> Callable[[F], F]:
    """Decorator for a hook implementation."""
    decorator: Callable[[F], F] = _hookimpl(trylast=trylast)
    return decorator
