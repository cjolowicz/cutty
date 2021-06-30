"""Functional tests for the update CLI."""
from pathlib import Path

import pygit2
from click.testing import CliRunner

from cutty.entrypoints.cli import main


def test_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0


def test_update(runner: CliRunner, repository: Path) -> None:
    """It applies changes from the template."""
    runner.invoke(
        main, ["create", "--no-input", str(repository)], catch_exceptions=False
    )

    # Update README.md.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")

    # Commit the changes.
    repo = pygit2.Repository(repository)
    signature = pygit2.Signature("you", "you@example.com")
    repo.index.add("{{ cookiecutter.project }}/README.md")
    tree = repo.index.write_tree()
    repo.create_commit(
        "HEAD",
        signature,
        signature,
        "Update README.md",
        tree,
        [repo.head.target],
    )

    runner.invoke(main, ["update"], catch_exceptions=False)
    assert (
        Path("example", "README.md").read_text() == "# example\nAn awesome project.\n"
    )
