"""Update a project."""
from pathlib import Path
from typing import Optional

from ..core import git
from ..core.application import Application


def _ensure_branch_exists(repository: git.Repository, branch: str) -> None:
    try:
        repository.rev_parse(branch, verify=True, quiet=True)
    except git.Error:
        (firstref,) = repository.rev_list(max_count=1, max_parents=0)
        repository.branch(branch, firstref)


def update(
    *,
    interactive: bool = False,
    revision: Optional[str] = None,
    directory: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Update a project from a Cookiecutter template."""
    application = Application.create(config_file=config_file)
    instance = git.Repository()

    with application.load_template_from_instance(
        instance.path, directory=directory, revision=revision
    ) as template:
        _ensure_branch_exists(instance, "template")

        with instance.worktree(
            instance.path / ".git" / "cutty" / instance.path.name,
            "template",
            checkout=False,
            force_remove=True,
        ) as project:
            application.generate_project(
                template,
                output_dir=project.path.parent,
                interactive=interactive,
                overwrite=True,
            )

            project.add(all=True)
            project.commit(
                message=f"Update template to {template.version}", verify=False
            )

            commit = project.rev_parse("HEAD")
            instance.cherrypick(commit)
