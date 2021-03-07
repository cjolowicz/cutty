"""Unit tests for cutty.adapters.click.prompts."""
from io import StringIO
from typing import Callable

import pytest

from cutty.adapters.click.prompts import ChoicePrompt
from cutty.adapters.click.prompts import ClickPromptFactory
from cutty.domain.prompts import PromptVariableBuilder
from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import RenderableValueLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.variables import Variable
from cutty.domain.varspecs import RenderableVariableSpecification
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


PatchStandardInput = Callable[[str], None]


@pytest.fixture
def patch_standard_input(monkeypatch: pytest.MonkeyPatch) -> PatchStandardInput:
    """Factory fixture that patches sys.stdin to produce a given text."""

    def _factory(text: str) -> None:
        monkeypatch.setattr("sys.stdin", StringIO(text))

    return _factory


@pytest.fixture
def value_loader(renderable_loader: RenderableLoader[str]) -> RenderableValueLoader:
    """Fixture for a renderable value loader."""
    return RenderableValueLoader(renderable_loader)


def test_noop_prompt() -> None:
    """It uses the default."""
    specification = RenderableVariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default=TrivialRenderable("example"),
        choices=(),
        interactive=False,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("project", "example")


def test_text_prompt(
    specification: Renderable[VariableSpecification[str]],
    patch_standard_input: PatchStandardInput,
) -> None:
    """It reads the value from stdin."""
    patch_standard_input("awesome-project\n")

    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("project", "awesome-project")


def test_choices_prompt(patch_standard_input: PatchStandardInput) -> None:
    """It reads a number from stdin."""
    patch_standard_input("2\n")

    specification = RenderableVariableSpecification(
        name="project",
        description="The name of the project",
        type=VariableType.STRING,
        default=TrivialRenderable("example"),
        choices=(TrivialRenderable("example"), TrivialRenderable("awesome-project")),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("project", "awesome-project")


def test_choices_prompt_invalid(
    specification: Renderable[VariableSpecification[str]],
) -> None:
    """It raises an exception when there are no choices."""
    prompt = ChoicePrompt(specification.render([]))
    with pytest.raises(ValueError):
        prompt.prompt()


def test_json_prompt(
    value_loader: RenderableValueLoader,
    patch_standard_input: PatchStandardInput,
) -> None:
    """It loads JSON from stdin."""
    patch_standard_input('{"name": "awesome"}\n')

    specification = RenderableVariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default=value_loader.load({"name": "example"}),
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("metadata", {"name": "awesome"})


def test_json_prompt_empty(
    value_loader: RenderableValueLoader,
    patch_standard_input: PatchStandardInput,
) -> None:
    """It returns the default."""
    patch_standard_input("\n")

    specification = RenderableVariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default=value_loader.load({"name": "example"}),
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("metadata", {"name": "example"})


def test_json_prompt_invalid(
    value_loader: RenderableValueLoader,
    patch_standard_input: PatchStandardInput,
) -> None:
    """It prompts again."""
    patch_standard_input('invalid\n"not a dict"\n{}\n')

    specification = RenderableVariableSpecification(
        name="metadata",
        description="metadata",
        type=VariableType.OBJECT,
        default=value_loader.load({"name": "example"}),
        choices=(),
        interactive=True,
    )
    factory = ClickPromptFactory()
    builder = PromptVariableBuilder(factory)

    [variable] = builder.build([specification])

    assert variable == Variable("metadata", {})
