"""Unit tests for cutty.variables.binders."""
from cutty.variables.binders import binddefault
from cutty.variables.binders import override
from cutty.variables.variables import GenericVariable


def test_override_empty(variable: GenericVariable[str]) -> None:
    """It does not override the variable."""
    binder = override(binddefault, [])
    binding = binder(variable)

    assert binding.name == variable.name
    assert binding.value == variable.default
