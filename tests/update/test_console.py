"""Test cases for the console module."""
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from cutty import git
from cutty.create.console import create
from cutty.update.console import update


def test_help_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(update, ["--help"])
    assert result.exit_code == 0


@pytest.fixture
def instance(
    runner: CliRunner, user_cache_dir: Path, template: git.Repository,
) -> git.Repository:
    """Fixture with a template instance."""
    runner.invoke(
        create, [str(template.path)], input="example",
    )

    instance = git.Repository.init(Path("example"))
    instance.add(all=True)
    instance.commit(message="Initial")
    instance.branch("template")

    os.chdir(instance.path)

    return instance


def test_update(
    runner: CliRunner, template: git.Repository, instance: git.Repository,
) -> None:
    """It updates the project from the template."""
    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.add(".")
    template.commit(message="Add LICENSE")
    template.tag("v1.1.0")

    result = runner.invoke(update)
    assert result.exit_code == 0


def test_interactive(
    runner: CliRunner, template: git.Repository, instance: git.Repository,
) -> None:
    """It reads interactive input."""
    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.add(".")
    template.commit(message="Add LICENSE")
    template.tag("v1.1.0")

    result = runner.invoke(update, ["--interactive"], input="example",)
    assert result.exit_code == 0
