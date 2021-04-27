"""Unit tests for cutty.plugins.domain.hooks."""
from cutty.plugins.domain.hooks import hook
from cutty.plugins.domain.hooks import implements


@hook
def examplehook(a: int, b: str) -> str:
    """Example hook."""


@hook
def anotherhook(x: float) -> int:
    """Another hook."""


def test_implement_hook() -> None:
    """It implements a hook."""

    @implements(examplehook)
    def exampleimplementation(a: int, b: str) -> str:
        """Example implementation."""
        return f"{a}: {b}"

    assert exampleimplementation(42, "teapot") == "42: teapot"
