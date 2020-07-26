"""Update a project."""
import json
from pathlib import Path
from typing import cast
from typing import Optional

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


def update(
    extra_context: StrMapping,
    *,
    interactive: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[str] = None,
    config_file: Optional[str] = None,
    default_config: bool = False,
) -> None:
    """Update a project from a Cookiecutter template."""
    config = get_user_config(config_file=config_file, default_config=default_config)
    previous_context_file = Path(".cookiecutter.json")
    if previous_context_file.exists():
        previous_context = _load_context(previous_context_file)
    else:
        previous_context = {}
    extra_context = {**previous_context, **extra_context}
    template = extra_context["_template"]
    repository = cache.repository(template)
    revision = (
        checkout if checkout is not None else (tags.find_latest(repository) or "HEAD")
    )

    with cache.worktree(template, revision) as worktree:
        repo_dir = (
            worktree.path if directory is None else worktree.path / Path(directory)
        )
        context_file = repo_dir / "cookiecutter.json"
        current_context = _load_context(context_file)
        if not interactive:
            interactive = bool(set(current_context) - set(previous_context))
        context = _create_context(
            context_file,
            template=template,
            extra_context=extra_context,
            no_input=not interactive,
            config=config,
        )
        repo_hash = cache.repository_hash(
            template, directory=Path(directory) if directory is not None else None
        )
        dump(config["replay_dir"], repo_hash, context)

        instance = git.Repository()
        project_path = instance.path / ".git" / "cookiecutter" / instance.path.name

        with instance.worktree(
            project_path, "template", checkout=False, force_remove=True
        ) as project:
            generate_files(
                repo_dir=str(repo_dir),
                context=context,
                overwrite_if_exists=True,
                output_dir=str(project.path.parent),
            )
            project.add(all=True)
            project.git("commit", f"--message=Update template to {revision}")
