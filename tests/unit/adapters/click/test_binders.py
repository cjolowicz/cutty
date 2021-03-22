"""Unit tests for cutty.adapters.click.binders."""
from collections.abc import Callable
from io import StringIO

import pytest

from cutty.adapters.click.binders import choiceprompt
from cutty.adapters.click.binders import prompt
from cutty.domain.binders import create_render_binder
from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.values import ValueType
from cutty.domain.variables import GenericVariable


PatchStandardInput = Callable[[str], None]


@pytest.fixture
def patch_standard_input(monkeypatch: pytest.MonkeyPatch) -> PatchStandardInput:
    """Factory fixture that patches sys.stdin to produce a given text."""

    def _factory(text: str) -> None:
        monkeypatch.setattr("sys.stdin", StringIO(text))

    return _factory


def test_noop_prompt(render: Renderer) -> None:
    """It uses the default."""
    variable = GenericVariable(
        name="project",
        description="The name of the project",
        type=ValueType.STRING,
        default="example",
        choices=(),
        interactive=False,
    )
    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("project", "example")


def test_text_prompt(
    render: Renderer,
    variable: GenericVariable[str],
    patch_standard_input: PatchStandardInput,
) -> None:
    """It reads the value from stdin."""
    patch_standard_input("awesome-project\n")

    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("project", "awesome-project")


def test_choices_prompt(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It reads a number from stdin."""
    patch_standard_input("2\n")

    variable = GenericVariable(
        name="project",
        description="The name of the project",
        type=ValueType.STRING,
        default="example",
        choices=("example", "awesome-project"),
        interactive=True,
    )
    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("project", "awesome-project")


def test_choices_prompt_invalid(
    render: Renderer, variable: GenericVariable[str]
) -> None:
    """It raises an exception when there are no choices."""
    with pytest.raises(ValueError):
        choiceprompt(variable)


def test_json_prompt(
    render: Renderer,
    patch_standard_input: PatchStandardInput,
) -> None:
    """It loads JSON from stdin."""
    patch_standard_input('{"name": "awesome"}\n')

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=ValueType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("metadata", {"name": "awesome"})


def test_json_prompt_empty(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It returns the default."""
    patch_standard_input("\n")

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=ValueType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("metadata", {"name": "example"})


def test_json_prompt_invalid(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It prompts again."""
    patch_standard_input('invalid\n"not a dict"\n{}\n')

    variable = GenericVariable(
        name="metadata",
        description="metadata",
        type=ValueType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    renderbind = create_render_binder(prompt)

    [binding] = renderbind(render, [variable])

    assert binding == Binding("metadata", {})
