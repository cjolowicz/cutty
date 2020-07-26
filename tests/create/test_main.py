"""Test cases for the console module."""
import shutil
from pathlib import Path

from click.testing import CliRunner

from cutty import git
from cutty.create.console import create


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(create, ["--help"])
    assert result.exit_code == 0


def test_create(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It generates a project from the template."""
    result = runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )
    assert result.exit_code == 0


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    text = text.replace(old, new)
    path.write_text(text)


def test_undefined_variable(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It displays an informative error message if a variable is undefined."""
    _replace(template.path / "cookiecutter.json", "project", "XXproject")

    template.add(".")
    template.git("commit", "--message=Typo")
    template.git("tag", "v1.0.1")

    result = runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )

    assert "has no attribute 'project'" in result.output


def test_output_directory_exists(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It displays an informative error message if the output directory exists."""
    Path("example").mkdir()

    result = runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )

    assert "already exists" in result.output


def test_checkout(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    template: git.Repository,
) -> None:
    """It checks out the specified revision."""
    _replace(
        template.path / "{{cookiecutter.project}}" / "README.md",
        "# {{cookiecutter.project}}",
        "## {{cookiecutter.project}}",
    )

    template.add(".")
    template.git("commit", "--message=Style")

    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}", "--checkout=master"],
        input="example",
        catch_exceptions=False,
    )

    assert (Path("example") / "README.md").read_text().startswith("## ")


def test_replay_dump(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    replay_dir: Path,
    template: git.Repository,
) -> None:
    """It dumps the context."""
    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input="example",
        catch_exceptions=False,
    )
    assert replay_dir.exists()


def test_replay_load(
    runner: CliRunner,
    user_cache_dir: Path,
    user_config_file: Path,
    replay_dir: Path,
    template: git.Repository,
) -> None:
    """It loads the context."""
    project = Path("replay-example")

    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}"],
        input=project.name,
        catch_exceptions=False,
    )

    shutil.rmtree(project)

    runner.invoke(
        create,
        [str(template.path), f"--config-file={user_config_file}", "--replay"],
        catch_exceptions=False,
    )

    assert project.exists()


def test_replay_with_no_input(runner: CliRunner, template: git.Repository) -> None:
    """It fails when passed --replay and --no-input."""
    result = runner.invoke(create, [str(template.path), "--replay", "--no-input"])
    assert result.exit_code == 1 and "replay" in result.output
