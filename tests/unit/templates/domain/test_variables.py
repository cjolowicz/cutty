"""Unit tests for cutty.templates.domain.variables."""
import pytest

from cutty.templates.domain.variables import validate
from cutty.templates.domain.variables import Variable


def test_validate_type_valid() -> None:
    """It does not raise if the value has the expected type."""
    variable = Variable(
        name="name",
        description="description",
        type=int,
        default=0,
        choices=(),
        interactive=True,
    )
    value = 1
    validate(value, variable)


def test_validate_type_invalid() -> None:
    """It raises if the value does not have the expected type."""
    variable = Variable(
        name="name",
        description="description",
        type=int,
        default=0,
        choices=(),
        interactive=True,
    )
    value = ""
    with pytest.raises(ValueError):
        validate(value, variable)


def test_validate_choice_valid() -> None:
    """It does not raise if the value is contained in the choices."""
    variable = Variable(
        name="name",
        description="description",
        type=int,
        default=0,
        choices=(0, 1, 2),
        interactive=True,
    )
    value = 1
    validate(value, variable)


def test_validate_choice_invalid() -> None:
    """It raises if the value is not contained in the choices."""
    variable = Variable(
        name="name",
        description="description",
        type=int,
        default=0,
        choices=(0, 1, 2),
        interactive=True,
    )
    value = 3
    with pytest.raises(ValueError):
        validate(value, variable)
