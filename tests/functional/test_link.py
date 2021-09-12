"""Functional tests for `cutty link`."""
from pathlib import Path

from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.util.files import chdir


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("link", "--help")


def test_project_config(runcutty: RunCutty, template: Path) -> None:
    """It adds a cutty.json to the project."""
    runcutty("cookiecutter", str(template))

    project = Repository.init(Path("example"))
    project.commit(message="Initial")

    with chdir(project.path):
        runcutty("link", str(template))

    assert (project.path / "cutty.json").is_file()
