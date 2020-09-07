"""Test cases for the console module."""
from pathlib import Path

from click.testing import CliRunner

from cutty.common import git
from cutty.legacy.create.console import create


def test_main_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(create, ["--help"])
    assert result.exit_code == 0


def test_create(
    runner: CliRunner, user_cache_dir: Path, template: git.Repository,
) -> None:
    """It generates a project from the template."""
    result = runner.invoke(
        create, [str(template.path)], input="example", catch_exceptions=False,
    )
    assert result.exit_code == 0


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    text = text.replace(old, new)
    path.write_text(text)


def test_undefined_variable(
    runner: CliRunner, user_cache_dir: Path, template: git.Repository,
) -> None:
    """It displays an informative error message if a variable is undefined."""
    _replace(template.path / "cookiecutter.json", "project", "XXproject")

    template.add(".")
    template.commit(message="Typo")
    template.tag("v1.0.1")

    result = runner.invoke(
        create, [str(template.path)], input="example", catch_exceptions=False,
    )

    assert "has no attribute 'project'" in result.output


def test_output_directory_exists(
    runner: CliRunner, user_cache_dir: Path, template: git.Repository,
) -> None:
    """It displays an informative error message if the output directory exists."""
    Path("example").mkdir()

    result = runner.invoke(
        create, [str(template.path)], input="example", catch_exceptions=False,
    )

    assert "already exists" in result.output


def test_checkout(
    runner: CliRunner, user_cache_dir: Path, template: git.Repository,
) -> None:
    """It checks out the specified revision."""
    _replace(
        template.path / "{{cookiecutter.project}}" / "README.md",
        "# {{cookiecutter.project}}",
        "## {{cookiecutter.project}}",
    )

    template.add(".")
    template.commit(message="Style")

    runner.invoke(
        create,
        [str(template.path), "--checkout=master"],
        input="example",
        catch_exceptions=False,
    )

    assert (Path("example") / "README.md").read_text().startswith("## ")
