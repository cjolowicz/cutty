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
def test_variable(name: str, value: Value) -> None:
    """It contains a name and value."""
    variable = Binding(name, value)
    assert variable.name == name
    assert variable.value == value
