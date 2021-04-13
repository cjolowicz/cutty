"""Unit tests for cutty.__main__."""
from typing import Any
from typing import Callable
from typing import Protocol

import click
import pytest
from click.testing import CliRunner

from cutty.__main__ import main


RunnerDecorator = Callable[[Callable[..., None]], Callable[..., None]]


class RunnerDecoratorFactory(Protocol):
    """Protocol."""

    def __call__(self, command: click.Command, *, monkeypatch: str) -> RunnerDecorator:
        """Invoke."""


@pytest.fixture
def runner(monkeypatch: pytest.MonkeyPatch) -> RunnerDecoratorFactory:
    """Fixture to patch the command-line interface."""
    _monkeypatch = monkeypatch

    def _decoratorfactory(
        command: click.Command, *, monkeypatch: str
    ) -> RunnerDecorator:
        def _decorator(innermain: Callable[..., None]) -> Callable[..., None]:
            _monkeypatch.setattr(monkeypatch, innermain)

            def _invoke(*args: str) -> None:
                result = CliRunner().invoke(command, args, catch_exceptions=False)
                if result.exit_code != 0:
                    raise Exception(
                        f"command exited with status {result.exit_code}:\n"
                        f"{result.output}"
                    )

            return _invoke

        return _decorator

    return _decoratorfactory


def test_extra_context_happy(runner: RunnerDecoratorFactory) -> None:
    """It parses additional arguments into key-value pairs."""

    @runner(main, monkeypatch="cutty.application.cookiecutter.main.main")
    def invoke(*args: Any, extra_context: dict[str, str], **kwargs: Any) -> None:
        """Main function."""
        assert extra_context == {"project": "example"}

    invoke("https://example.com/repository.git", "project=example")


def test_extra_context_invalid(runner: RunnerDecoratorFactory) -> None:
    """It raises an exception if additional arguments cannot be parsed."""

    @runner(main, monkeypatch="cutty.application.cookiecutter.main.main")
    def invoke(*args: Any, **kwargs: Any) -> None:
        pass

    with pytest.raises(Exception):
        invoke("https://example.com/repository.git", "invalid")
