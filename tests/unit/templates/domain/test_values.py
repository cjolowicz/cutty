"""Unit tests for cutty.templates.domain.values."""
from typing import Union

import pytest
from hypothesis import given
from hypothesis import infer
from hypothesis import settings

from cutty.templates.domain.values import getvaluetype
from cutty.templates.domain.values import ValueType


Scalar = Union[bool, int, float, str]


@given(value=infer)
def test_getvaluetype_boolean(value: bool) -> None:
    """It is BOOLEAN."""
    assert getvaluetype(value) is ValueType.BOOLEAN


@given(value=infer)
def test_getvaluetype_integer(value: Union[int, float]) -> None:
    """It is NUMBER."""
    assert getvaluetype(value) is ValueType.NUMBER


@given(value=infer)
def test_getvaluetype_string(value: str) -> None:
    """It is STRING."""
    assert getvaluetype(value) is ValueType.STRING


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_array_simple(value: list[Scalar]) -> None:
    """It is ARRAY."""
    assert getvaluetype(value) is ValueType.ARRAY


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_array_nested(value: list[list[Scalar]]) -> None:
    """It is ARRAY."""
    assert getvaluetype(value) is ValueType.ARRAY


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_array_mixed(value: list[dict[str, Scalar]]) -> None:
    """It is ARRAY."""
    assert getvaluetype(value) is ValueType.ARRAY


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_object_simple(value: dict[str, Scalar]) -> None:
    """It is OBJECT."""
    assert getvaluetype(value) is ValueType.OBJECT


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_object_nested(value: dict[str, dict[str, Scalar]]) -> None:
    """It is OBJECT."""
    assert getvaluetype(value) is ValueType.OBJECT


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_object_mixed(value: dict[str, list[Scalar]]) -> None:
    """It is OBJECT."""
    assert getvaluetype(value) is ValueType.OBJECT


@given(value=infer)
def test_getvaluetype_invalid_exception(value: Exception) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        getvaluetype(value)


@given(value=infer)
def test_getvaluetype_invalid_bytes(value: bytes) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        getvaluetype(value)


@pytest.mark.xfail(
    reason="known issue: getvaluetype does not check types of array elements"
)
@given(value=infer)
def test_getvaluetype_invalid_array(value: list[bytes]) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        getvaluetype(value)


@pytest.mark.xfail(reason="known issue: getvaluetype does not check types of dict keys")
@given(value=infer)
def test_getvaluetype_invalid_object_key(value: dict[int, str]) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        getvaluetype(value)


@pytest.mark.xfail(
    reason="known issue: getvaluetype does not check types of dict values"
)
@given(value=infer)
def test_getvaluetype_invalid_object_value(value: dict[str, bytes]) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        getvaluetype(value)
