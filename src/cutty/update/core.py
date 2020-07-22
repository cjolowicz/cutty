"""Update a project."""
import json
from pathlib import Path
from typing import cast

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_files
from cookiecutter.replay import dump

from .. import cache
from .. import git
from .. import tags
from ..create.core import _create_context
from ..types import StrMapping


def _load_context(context_file: Path) -> StrMapping:
    with context_file.open() as io:
        return cast(StrMapping, json.load(io))


def update(extra_context: StrMapping) -> None:
    """Update a project from a Cookiecutter template."""
    config = get_user_config()
    previous_context = _load_context(Path(".cookiecutter.json"))
    extra_context = {**previous_context, **extra_context}
    template = extra_context["_template"]
    repository = cache.repository(template)
    revision = tags.find_latest(repository) or "HEAD"

    with cache.worktree(template, revision) as worktree:
        context_file = worktree.path / "cookiecutter.json"
        current_context = _load_context(context_file)
        no_input = not (set(current_context) - set(previous_context))
        context = _create_context(
            context_file,
            template=template,
            extra_context=extra_context,
            no_input=no_input,
            config=config,
        )
        repo_hash = cache.repository_hash(template)
        dump(config["replay_dir"], repo_hash, context)

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
