"""Unit tests for cutty.templates.domain.values."""
import pytest
from hypothesis import given
from hypothesis import infer
from hypothesis import settings

from cutty.templates.domain.values import getvaluetype
from cutty.templates.domain.values import ValueType


@given(value=infer)
def test_getvaluetype_string(value: str) -> None:
    """It is STRING."""
    assert getvaluetype(value) is ValueType.STRING


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_object_simple(value: dict[str, str]) -> None:
    """It is OBJECT."""
    assert getvaluetype(value) is ValueType.OBJECT


@given(value=infer)
@settings(max_examples=10)  # type: ignore[misc]
def test_getvaluetype_object_nested(value: dict[str, dict[str, str]]) -> None:
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
