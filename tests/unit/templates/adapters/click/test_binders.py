"""Unit tests for cutty.templates.adapters.click.binders."""
from collections.abc import Callable
from io import StringIO

import pytest

from cutty.templates.adapters.click.binders import choiceprompt
from cutty.templates.adapters.click.binders import prompt
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.variables import GenericVariable


PatchStandardInput = Callable[[str], None]


@pytest.fixture
def patch_standard_input(monkeypatch: pytest.MonkeyPatch) -> PatchStandardInput:
    """Factory fixture that patches sys.stdin to produce a given text."""

    def _factory(text: str) -> None:
        monkeypatch.setattr("sys.stdin", StringIO(text))

    return _factory


def test_noop_prompt() -> None:
    """It uses the default."""
    variable = GenericVariable(
        name="project",
        description="The name of the project",
        type=str,
        default="example",
        choices=(),
        interactive=False,
    )
    assert prompt(variable) == Binding("project", "example")


def test_text_prompt(
    variable: GenericVariable[str], patch_standard_input: PatchStandardInput
) -> None:
    """It reads the value from stdin."""
    patch_standard_input("awesome-project\n")

    assert prompt(variable) == Binding("project", "awesome-project")


def test_choices_prompt(patch_standard_input: PatchStandardInput) -> None:
    """It reads a number from stdin."""
    patch_standard_input("2\n")

    variable = GenericVariable(
        name="project",
        description="The name of the project",
        type=str,
        default="example",
        choices=("example", "awesome-project"),
        interactive=True,
    )
    assert prompt(variable) == Binding("project", "awesome-project")


def test_choices_prompt_invalid(variable: GenericVariable[str]) -> None:
    """It raises an exception when there are no choices."""
    with pytest.raises(ValueError):
        choiceprompt(variable)


def test_json_prompt(patch_standard_input: PatchStandardInput) -> None:
    """It loads JSON from stdin."""
    patch_standard_input('{"name": "awesome"}\n')

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=dict,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    assert prompt(variable) == Binding("metadata", {"name": "awesome"})


def test_json_prompt_empty(patch_standard_input: PatchStandardInput) -> None:
    """It returns the default."""
    patch_standard_input("\n")

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=dict,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    assert prompt(variable) == Binding("metadata", {"name": "example"})


def test_json_prompt_invalid(patch_standard_input: PatchStandardInput) -> None:
    """It prompts again."""
    patch_standard_input('invalid\n"not a dict"\n{}\n')

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=dict,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    assert prompt(variable) == Binding("metadata", {})
