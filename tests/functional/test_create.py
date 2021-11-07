"""Functional tests for the create CLI."""
import string
from pathlib import Path

import pytest

from cutty.projects.config import PROJECT_CONFIG_FILE
from cutty.projects.config import readprojectconfigfile
from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.conftest import RunCuttyError
from tests.util.files import project_files
from tests.util.files import template_files
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import updatefile
from tests.util.keys import BACKSPACE
from tests.util.keys import RETURN


EXTRA = {Path("post_gen_project"), Path(PROJECT_CONFIG_FILE)}


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("create", "--help")


def test_input(runcutty: RunCutty, template: Path) -> None:
    """It binds project variables from user input."""
    runcutty(
        "create",
        str(template),
        input=BACKSPACE * len("example") + "foobar" + RETURN * 3,
    )

    assert Path("foobar", "README.md").read_text() == "# foobar\n"


def test_hook(runcutty: RunCutty, template: Path) -> None:
    """It runs hooks."""
    runcutty("create", "--non-interactive", str(template))

    assert Path("example", "post_gen_project").is_file()


def test_files(runcutty: RunCutty, template: Path) -> None:
    """It renders the project files."""
    runcutty("create", "--non-interactive", str(template))

    assert template_files(template) == project_files("example") - EXTRA


def test_cutty_json(runcutty: RunCutty, template: Path) -> None:
    """It creates a cutty.json file."""
    runcutty("create", "--non-interactive", str(template))

    assert Path("example", PROJECT_CONFIG_FILE).is_file()


def test_cutty_json_already_exists(runcutty: RunCutty, template: Path) -> None:
    """It raises an exception if the template generates cutty.json."""
    updatefile(template / "{{ cookiecutter.project }}" / PROJECT_CONFIG_FILE)

    with pytest.raises(FileExistsError):
        runcutty("create", "--non-interactive", str(template))


def test_cwd(runcutty: RunCutty, template: Path) -> None:
    """It creates the project directory in the output directory."""
    outputdir = Path("output")
    outputdir.mkdir()

    runcutty("create", "--non-interactive", f"--cwd={outputdir}", str(template))

    assert template_files(template) == project_files(outputdir / "example") - EXTRA


def test_inplace(runcutty: RunCutty, template: Path) -> None:
    """It generates the project files in the current directory."""
    runcutty("create", "--non-interactive", "--in-place", str(template))

    assert template_files(template) == project_files(".") - EXTRA


def test_directory(runcutty: RunCutty, template: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty(
        "create",
        "--non-interactive",
        f"--template-directory={directory}",
        str(template),
    )

    assert template_files(template / "a") == project_files("example") - EXTRA


def test_commit_message_template(runcutty: RunCutty, template: Path) -> None:
    """It includes the template name in the commit message."""
    runcutty("create", "--non-interactive", str(template))
    repository = Repository.open(Path("example"))
    assert template.name in repository.head.commit.message


def test_commit_message_revision(runcutty: RunCutty, template: Path) -> None:
    """It includes the revision in the commit message."""
    revision = Repository.open(template).head.commit.id

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    runcutty("create", "--non-interactive", f"--revision={revision}", str(template))

    repository = Repository.open(Path("example"))

    assert str(revision)[:7] in repository.head.commit.message


def test_cutty_error(runcutty: RunCutty) -> None:
    """It prints an error message for known exceptions."""
    with pytest.raises(Exception, match="unknown location"):
        runcutty("create", "--non-interactive", "invalid://location")


def test_empty_template(emptytemplate: Path, runcutty: RunCutty) -> None:
    """It exits with a non-zero status code."""
    with pytest.raises(RunCuttyError):
        runcutty("create", "--non-interactive", str(emptytemplate))


def test_no_branches(runcutty: RunCutty, template: Path) -> None:
    """It does not create additional branches."""
    project = Repository.init(Path("example"))
    project.commit()

    branches = list(project.heads)

    runcutty(
        "create",
        "--non-interactive",
        f"--cwd={project.path}",
        "--in-place",
        str(template),
    )

    assert branches == list(project.heads)


def test_existing_files(runcutty: RunCutty, template: Path) -> None:
    """It does not commit existing files."""
    existing = Path("example", "do-not-commit-this-file")
    existing.parent.mkdir()
    existing.touch()

    runcutty("create", "--non-interactive", str(template))

    project = Repository.open(existing.parent)
    assert existing.name not in project.head.commit.tree


def test_untracked_files(runcutty: RunCutty, template: Path) -> None:
    """It does not commit untracked files."""
    project = Repository.init(Path("example"))

    untracked = project.path / "untracked-file"
    untracked.touch()

    runcutty("create", "--non-interactive", str(template))

    assert untracked.name not in project.head.commit.tree


def test_untracked_project_files(runcutty: RunCutty, template: Path) -> None:
    """It bails out to avoid overwriting uncommitted changes."""
    project = Repository.init(Path("example"))

    untracked = project.path / "cutty.json"
    untracked.touch()

    with pytest.raises(Exception, match="uncommitted change"):
        runcutty("create", "--non-interactive", str(template))

    assert {untracked.relative_to(project.path)} == project_files(project.path)


def test_existing_project_files(runcutty: RunCutty, template: Path) -> None:
    """It does not overwrite existing files."""
    project = Path("example")
    project.mkdir()

    existing = project / "cutty.json"
    existing.touch()

    with pytest.raises(Exception, match="uncommitted change"):
        runcutty("create", "--non-interactive", str(template))

    assert {existing.relative_to(project)} == project_files(project)


def test_conflict(runcutty: RunCutty, template: Path) -> None:
    """It produces conflict markers if files have conflicting changes."""
    project = Repository.init(Path("example"))
    conflicting = project.path / "README.md"

    updatefile(conflicting, "teapot")

    with pytest.raises(Exception, match="conflict"):
        runcutty("create", "--non-interactive", str(template))

    assert ">>>>" in conflicting.read_text()


def test_conflict_cutty_json(runcutty: RunCutty, template: Path) -> None:
    """It resolves conflicts in cutty.json in favor of the new version."""
    project = Repository.init(Path("example"))
    conflicting = project.path / "cutty.json"

    updatefile(conflicting, "null")

    runcutty("create", "--non-interactive", str(template))

    assert ">>>>" not in conflicting.read_text()


def test_commit_hash(runcutty: RunCutty, template: Path) -> None:
    """It stores the commit hash."""
    runcutty("create", "--non-interactive", str(template))

    revision = readprojectconfigfile(Path("example")).revision

    assert (
        revision is not None
        and len(revision) == 40
        and all(c in string.hexdigits for c in revision)
    )
