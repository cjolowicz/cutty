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
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> git.Repository:
    """Fixture with a template instance."""
    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
    )

    instance = git.Repository.init(Path("example"))
    instance.add(all=True)
    instance.commit(message="Initial")
    instance.git("branch", "template")

    os.chdir(instance.path)

    return instance


def test_update(
    runner: CliRunner,
    user_config_file: Path,
    template: git.Repository,
    instance: git.Repository,
) -> None:
    """It updates the project from the template."""
    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.add(".")
    template.commit(message="Add LICENSE")
    template.git("tag", "v1.1.0")

    result = runner.invoke(update, [f"--config-file={user_config_file}"])
    assert result.exit_code == 0


def test_interactive(
    runner: CliRunner,
    user_config_file: Path,
    template: git.Repository,
    instance: git.Repository,
) -> None:
    """It reads interactive input."""
    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.add(".")
    template.commit(message="Add LICENSE")
    template.git("tag", "v1.1.0")

    result = runner.invoke(
        update, [f"--config-file={user_config_file}", "--interactive"], input="example",
    )
    assert result.exit_code == 0


def test_no_previous_context(
    runner: CliRunner,
    user_config_file: Path,
    template: git.Repository,
    instance: git.Repository,
) -> None:
    """It updates the project from the template."""
    template.git(
        "rm", str(template.path / "{{cookiecutter.project}}" / ".cookiecutter.json")
    )
    template.commit(message="Remove .cookiecutter.json")
    template.git("tag", "v1.1.0")

    result = runner.invoke(update, [f"--config-file={user_config_file}"])
    git.Repository().git("merge", "template")

    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.add(".")
    template.commit(message="Add LICENSE")
    template.git("tag", "v1.2.0")

    result = runner.invoke(
        update,
        [f"--config-file={user_config_file}", f"_template={template.path}"],
        input="example",
    )
    assert result.exit_code == 0
