"""Unit tests for the bindings module."""
import pytest

from cutty.domain.bindings import Binding
from cutty.domain.bindings import Value


@pytest.mark.parametrize(
    "name,value",
    [
        ("optional", None),
        ("generate_cli", True),
        ("year", 2021),
        ("pi", 3.14),
        ("project", "example"),
        ("licenses", ["MIT", "GPLv3"]),
        ("metadata", {"name": "example"}),
    ],
)
def test_binding(name: str, value: Value) -> None:
    """It contains a name and value."""
    binding = Binding(name, value)
    assert binding.name == name
    assert binding.value == value
