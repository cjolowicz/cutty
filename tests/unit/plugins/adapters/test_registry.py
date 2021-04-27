"""Unit tests for cutty.plugins.adapters.fake."""
from typing import Optional

from cutty.plugins.adapters.fake import FakeRegistry
from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry


@hook
def examplehook(a: int, b: str) -> str:
    """Example hook."""


@hook
def anotherhook(x: float) -> int:
    """Another hook."""


def test_dispatches_none() -> None:
    """It returns an empty list when dispatching without implementations."""
    registry: Registry = FakeRegistry()
    dispatch = registry.bind(examplehook)

    assert dispatch(42, "teapot") == []


def test_dispatches_some() -> None:
    """It returns a result list when dispatching to implementations."""

    @implements(examplehook)
    def exampleimplementation1(a: int, b: str) -> str:
        """First implementation."""
        return f"1: {a}-{b}"

    @implements(examplehook)
    def exampleimplementation2(a: int, b: str) -> str:
        """Second implementation."""
        return f"2: {a}-{b}"

    registry: Registry = FakeRegistry()
    dispatch = registry.bind(examplehook)

    registry.register(exampleimplementation1)
    registry.register(exampleimplementation2)

    assert dispatch(42, "teapot") == ["2: 42-teapot", "1: 42-teapot"]


def test_dispatches_registered() -> None:
    """It dispatches only to implementations registered for the hook."""

    @implements(examplehook)
    def exampleimplementation(a: int, b: str) -> str:
        """Implementation of examplehook."""
        return f"{a}-{b}"

    @implements(anotherhook)
    def anotherimplementation(x: float) -> int:
        """Implementation of anotherhook."""
        return round(1)

    registry: Registry = FakeRegistry()
    dispatch = registry.bind(examplehook)
    registry.bind(anotherhook)

    registry.register(exampleimplementation)
    registry.register(anotherimplementation)

    assert dispatch(42, "teapot") == ["42-teapot"]


@hook(firstresult=True)
def firstresulthook(x: int) -> Optional[str]:
    """Hook that returns the first result of an implementation."""


def test_firstresulthook_none() -> None:
    """It returns None."""
    registry: Registry = FakeRegistry()
    dispatch = registry.bind(firstresulthook)

    assert dispatch(3) is None


def test_firstresulthook_some() -> None:
    """It returns the first result that is not None."""

    @implements(firstresulthook)
    def nothing(x: int) -> Optional[str]:
        """Return None."""
        return None

    @implements(firstresulthook)
    def chain(x: int) -> Optional[str]:
        """Return a chain of x's."""
        return "x" * x

    @implements(firstresulthook)
    def teapot(x: int) -> Optional[str]:
        """Return a teapot."""
        return "teapot"

    registry: Registry = FakeRegistry()
    dispatch = registry.bind(firstresulthook)

    registry.register(teapot)
    registry.register(chain)
    registry.register(nothing)

    assert dispatch(3) == "xxx"
