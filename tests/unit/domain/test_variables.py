"""Unit tests for the variables module."""
import pytest

from cutty.domain.variables import Value
from cutty.domain.variables import Variable


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
    variable = Variable(name, value)
    assert variable.name == name
    assert variable.value == value
