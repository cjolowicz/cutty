"""Test cases for the console module."""
import os
from pathlib import Path

from click.testing import CliRunner

from cutty import git
from cutty.create.console import create
from cutty.update.console import update


def test_help_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(update, ["--help"])
    assert result.exit_code == 0


def test_update(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It generates a project from the template."""
    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )

    instance = git.Repository.init(Path("example"))
    instance.git("add", "--all")
    instance.git("commit", "--message=Initial")
    instance.git("branch", "template")

    os.chdir(instance.path)

    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.git("add", ".")
    template.git("commit", "--message=Add LICENSE")
    template.git("tag", "v1.1.0")

    result = runner.invoke(update, [f"--config-file={user_config_file}"])
    assert result.exit_code == 0


def test_interactive(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It generates a project from the template."""
    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )

    instance = git.Repository.init(Path("example"))
    instance.git("add", "--all")
    instance.git("commit", "--message=Initial")
    instance.git("branch", "template")

    os.chdir(instance.path)

    (template.path / "{{cookiecutter.project}}" / "LICENSE").touch()
    template.git("add", ".")
    template.git("commit", "--message=Add LICENSE")
    template.git("tag", "v1.1.0")

    result = runner.invoke(
        update, [f"--config-file={user_config_file}", "--interactive"], input="example",
    )
    assert result.exit_code == 0
