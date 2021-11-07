"""Unit tests for prompts using questionary."""
import json
from collections.abc import Iterator
from dataclasses import replace

import pytest
from prompt_toolkit.input.base import PipeInput
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output import DummyOutput

from cutty.variables.domain.binders import Binder
from cutty.variables.domain.bindings import GenericBinding
from cutty.variables.domain.variables import GenericVariable
from cutty.variables.prompts import createprompt
from tests.util.keys import BACKSPACE
from tests.util.keys import ESCAPE
from tests.util.keys import RETURN


@pytest.fixture
def pipe() -> Iterator[PipeInput]:
    """Fixture for an input pipe."""
    pipe = create_pipe_input()
    yield pipe

    pipe.close()


@pytest.fixture
def prompt(pipe: PipeInput) -> Binder:
    """Fixture for a questionary prompt."""
    return createprompt(input=pipe, output=DummyOutput())


def test_noninteractive(prompt: Binder, variable: GenericVariable[str]) -> None:
    """It binds the variable to its default."""
    variable = replace(variable, interactive=False)

    binding = prompt(variable)

    assert GenericBinding(variable.name, variable.default) == binding


def test_text(prompt: Binder, pipe: PipeInput, variable: GenericVariable[str]) -> None:
    """It reads free text from the user."""
    pipe.send_text(BACKSPACE * len(variable.default))
    pipe.send_text("awesome")
    pipe.send_text(RETURN)

    binding = prompt(variable)

    assert GenericBinding(variable.name, "awesome") == binding


def test_text_default(
    prompt: Binder, pipe: PipeInput, variable: GenericVariable[str]
) -> None:
    """It returns the default."""
    pipe.send_text(RETURN)

    binding = prompt(variable)

    assert GenericBinding(variable.name, variable.default) == binding


def test_choices(
    prompt: Binder, pipe: PipeInput, variable: GenericVariable[str]
) -> None:
    """It accepts the position of a valid choice."""
    variable = replace(variable, choices=("example", "awesome"))

    pipe.send_text("2")
    pipe.send_text(RETURN)

    binding = prompt(variable)

    assert GenericBinding(variable.name, "awesome") == binding


def test_choices_default(
    prompt: Binder, pipe: PipeInput, variable: GenericVariable[str]
) -> None:
    """It selects the default."""
    variable = replace(variable, choices=("example", "awesome"), default="awesome")

    pipe.send_text(RETURN)

    binding = prompt(variable)

    assert GenericBinding(variable.name, "awesome") == binding


@pytest.fixture
def dictvariable() -> GenericVariable[dict[str, str]]:
    """Fixture for a dict variable."""
    name, default = "metadata", {"name": "example"}
    return GenericVariable(name, name, type(default), default, (), True)


def test_json(
    prompt: Binder, pipe: PipeInput, dictvariable: GenericVariable[dict[str, str]]
) -> None:
    """It loads JSON from the user input."""
    text = json.dumps(dictvariable.default, indent=2)

    pipe.send_text(BACKSPACE * len(text))
    pipe.send_text('{"name": "awesome"}')
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    binding = prompt(dictvariable)

    assert GenericBinding(dictvariable.name, {"name": "awesome"}) == binding


def test_json_default(
    prompt: Binder, pipe: PipeInput, dictvariable: GenericVariable[dict[str, str]]
) -> None:
    """It returns the default."""
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    binding = prompt(dictvariable)

    assert GenericBinding(dictvariable.name, dictvariable.default) == binding


def test_json_invalid(
    prompt: Binder, pipe: PipeInput, dictvariable: GenericVariable[dict[str, str]]
) -> None:
    """It does not accept the input unless it is valid JSON."""
    text = json.dumps(dictvariable.default, indent=2)

    pipe.send_text(BACKSPACE * len(text))
    pipe.send_text("invalid")
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    pipe.send_text(BACKSPACE * len("invalid"))
    pipe.send_text("{}")
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    binding = prompt(dictvariable)

    assert GenericBinding(dictvariable.name, {}) == binding


def test_json_not_dict(
    prompt: Binder, pipe: PipeInput, dictvariable: GenericVariable[dict[str, str]]
) -> None:
    """It does not accept the input unless it is a JSON object."""
    text = json.dumps(dictvariable.default, indent=2)

    pipe.send_text(BACKSPACE * len(text))
    pipe.send_text("null")
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    pipe.send_text(BACKSPACE * len("null"))
    pipe.send_text("{}")
    pipe.send_text(ESCAPE)
    pipe.send_text(RETURN)

    binding = prompt(dictvariable)

    assert GenericBinding(dictvariable.name, {}) == binding
