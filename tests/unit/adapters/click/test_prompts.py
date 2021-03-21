"""Unit tests for cutty.adapters.click.prompts."""
from collections.abc import Callable
from io import StringIO

import pytest

from cutty.adapters.click.prompts import ChoicePrompt
from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


PatchStandardInput = Callable[[str], None]


@pytest.fixture
def patch_standard_input(monkeypatch: pytest.MonkeyPatch) -> PatchStandardInput:
    """Factory fixture that patches sys.stdin to produce a given text."""

    def _factory(text: str) -> None:
        monkeypatch.setattr("sys.stdin", StringIO(text))

    return _factory


def test_noop_prompt(render: Renderer) -> None:
    """It uses the default."""
    specification = VariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default="example",
        choices=(),
        interactive=False,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("project", "example")


def test_text_prompt(
    render: Renderer,
    specification: VariableSpecification[str],
    patch_standard_input: PatchStandardInput,
) -> None:
    """It reads the value from stdin."""
    patch_standard_input("awesome-project\n")

    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("project", "awesome-project")


def test_choices_prompt(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It reads a number from stdin."""
    patch_standard_input("2\n")

    specification = VariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default="example",
        choices=("example", "awesome-project"),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("project", "awesome-project")


def test_choices_prompt_invalid(
    render: Renderer, specification: VariableSpecification[str]
) -> None:
    """It raises an exception when there are no choices."""
    prompt = ChoicePrompt(specification)
    with pytest.raises(ValueError):
        prompt.prompt()


def test_json_prompt(
    render: Renderer,
    patch_standard_input: PatchStandardInput,
) -> None:
    """It loads JSON from stdin."""
    patch_standard_input('{"name": "awesome"}\n')

    specification = VariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("metadata", {"name": "awesome"})


def test_json_prompt_empty(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It returns the default."""
    patch_standard_input("\n")

    specification = VariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("metadata", {"name": "example"})


def test_json_prompt_invalid(
    render: Renderer, patch_standard_input: PatchStandardInput
) -> None:
    """It prompts again."""
    patch_standard_input('invalid\n"not a dict"\n{}\n')

    specification = VariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default={"name": "example"},
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification], [], render)

    assert variable == Variable("metadata", {})
