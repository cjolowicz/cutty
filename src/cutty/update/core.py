"""Update a project."""
import json
from pathlib import Path

from cookiecutter.generate import generate_files

from .. import cache
from .. import git
from .. import tags


def update() -> None:
    """Update a project from a Cookiecutter template."""
    context_file = Path(".cookiecutter.json")
    with context_file.open() as io:
        context = json.load(io)
    template = context["_template"]
    repository = cache.repository(template)
    revision = tags.find_latest(repository) or "HEAD"
    with cache.worktree(template, revision) as worktree:
        instance = git.Repository()
        project_path = instance.path / ".git" / "cookiecutter" / instance.path.name

        with instance.worktree(project_path, "template", force_remove=True) as project:
            generate_files(
                repo_dir=str(worktree.path),
                context=context,
                overwrite_if_exists=True,
                output_dir=str(project.path.parent),
            )
            project.git("add", "--all")
            project.git("commit", f"--message=Update template to {revision}")
