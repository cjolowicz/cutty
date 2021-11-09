"""Unit tests for cutty.variables.domain.binders."""
from cutty.variables.domain.binders import binddefault
from cutty.variables.domain.binders import override
from cutty.variables.domain.variables import GenericVariable


def test_override_empty(variable: GenericVariable[str]) -> None:
    """It does not override the variable."""
    binder = override(binddefault, [])
    binding = binder(variable)

    assert binding.name == variable.name
    assert binding.value == variable.default
