"""Unit tests for the renderables module."""
import pytest

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableDict
from cutty.domain.renderables import RenderableList
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.variables import Value


def test_trivial_renderable_none() -> None:
    """It returns None."""
    renderable = TrivialRenderable(None)
    assert renderable.render([]) is None


def test_trivial_renderable_non_none() -> None:
    """It returns the value."""
    renderable = TrivialRenderable(42)
    assert renderable.render([]) == 42


def test_renderable_list() -> None:
    """It renders each item."""
    renderable: Renderable[Value] = TrivialRenderable("example")
    renderable = RenderableList([renderable])
    assert renderable.render([]) == ["example"]


def test_renderable_dict() -> None:
    """It renders each key and value."""
    key = TrivialRenderable("key")
    value = TrivialRenderable(42)
    renderable = RenderableDict([(key, value)])
    assert renderable.render([]) == {"key": 42}


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            {"key": 42},
            {"key": "42"},
        ),
        (
            [1, 2, "three"],
            ["1", "2", "three"],
        ),
    ],
)
def test_renderable_loader(
    renderable_loader: RenderableLoader, value: Value, expected: Value
) -> None:
    """It returns a renderable that renders as expected."""
    renderable = renderable_loader.load(value)
    assert expected == renderable.render([])
