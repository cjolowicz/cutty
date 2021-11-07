"""Fixtures for functional tests."""
import json
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent
from typing import Optional
from typing import Protocol

import pytest
from click.testing import CliRunner
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.input.base import PipeInput
from prompt_toolkit.output import DummyOutput

from cutty.entrypoints.cli import main
from cutty.util.git import Repository


@pytest.fixture
def pipeinput() -> Iterator[PipeInput]:
    """Fixture for piping input to prompt_toolkit."""
    pipe = create_pipe_input()
    try:
        with create_app_session(input=pipe, output=DummyOutput()):
            yield pipe
    finally:
        pipe.close()


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


class RunCutty(Protocol):
    """Invoke the cutty CLI."""

    def __call__(self, *args: str, input: Optional[str] = None) -> str:
        """Invoke the cutty CLI."""


class RunCuttyError(Exception):
    """The cutty CLI exited with a non-zero status."""


@pytest.fixture
def runcutty(runner: CliRunner, pipeinput: PipeInput) -> RunCutty:
    """Fixture for invoking the cutty CLI."""

    def _run(*args: str, input: Optional[str] = None) -> str:
        if input is not None:
            pipeinput.send_text(input)

        result = runner.invoke(main, args, catch_exceptions=False)

        if result.exit_code != 0:
            raise RunCuttyError(result.output or str(result.exit_code))

        return result.output

    return _run


@pytest.fixture
def template_directory(tmp_path: Path) -> Path:
    """Fixture for a template directory."""

    def create(path: Path, text: str) -> None:
        """Create a file with the given path and contents."""
        text = dedent(text).removeprefix("\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    template = tmp_path / "template-42"
    context = {
        "project": "example",
        "license": ["MIT", "GPL-3.0", "Apache-2.0"],
        "cli": True,
        "_extensions": ["jinja2_time.TimeExtension"],
    }

    create(template / "cookiecutter.json", json.dumps(context))

    create(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        """,
    )

    create(
        template / "hooks" / "post_gen_project.py",
        """
        open("post_gen_project", mode="w")
        """,
    )

    return template


@pytest.fixture
def template(template_directory: Path) -> Path:
    """Fixture for a template repository."""
    repository = Repository.init(template_directory)
    repository.commit(message="Initial")
    return template_directory


@pytest.fixture
def emptytemplate(tmp_path: Path) -> Path:
    """Fixture for a template without project files."""
    template = tmp_path / "template"
    template.mkdir()

    (template / "cookiecutter.json").write_text('{"project": "project"}')
    (template / "{{ cookiecutter.project }}").mkdir()

    return template
