"""Unit tests for the bindings module."""
from typing import Any

import pytest

from cutty.templates.domain.bindings import Binding


@pytest.mark.parametrize(
    "name,value",
    [
        ("project", "example"),
        ("licenses", ["MIT", "GPLv3"]),
        ("metadata", {"name": "example"}),
    ],
)
def test_binding(name: str, value: Any) -> None:
    """It contains a name and value."""
    binding = Binding(name, value)
    assert binding.name == name
    assert binding.value == value
