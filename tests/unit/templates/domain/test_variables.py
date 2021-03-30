"""Unit tests for cutty.templates.domain.variables."""
from typing import Any

import pytest
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies

from cutty.templates.domain.variables import validate
from cutty.templates.domain.variables import Variable
from tests.unit.templates.domain.strategies import values
from tests.unit.templates.domain.strategies import variables


@given(
    value=values(valuetype=int),
    variable=variables(valuetype=int, choices=()),
)
def test_validate_type_valid(value: Any, variable: Variable) -> None:
    """It does not raise if the value has the expected type."""
    validate(value, variable)


@given(
    value=values(valuetype=str),
    variable=variables(valuetype=int, choices=()),
)
def test_validate_type_invalid(value: Any, variable: Variable) -> None:
    """It raises if the value does not have the expected type."""
    with pytest.raises(ValueError):
        validate(value, variable)


@given(
    value=values(valuetype=int),
    variable=variables(valuetype=int, choices=()),
)
def test_validate_choices_empty(value: Any, variable: Variable) -> None:
    """It does not raise if the variable does not specify choices."""
    validate(value, variable)


@given(variable=variables(), data=strategies.data())
def test_validate_choice_valid(
    variable: Variable,
    data: strategies.DataObject,
) -> None:
    """It does not raise if the value is contained in the choices."""
    assume(variable.choices)
    value = data.draw(strategies.sampled_from(variable.choices))
    validate(value, variable)


@given(
    value=values(valuetype=int),
    variable=variables(valuetype=int),
)
def test_validate_choice_invalid(value: Any, variable: Variable) -> None:
    """It raises if the value is not contained in the choices."""
    assume(variable.choices and value not in variable.choices)
    with pytest.raises(ValueError):
        validate(value, variable)
