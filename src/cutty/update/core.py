"""Update a project."""
from pathlib import Path
from typing import Optional

from cookiecutter.generate import generate_files
from cookiecutter.repository import expand_abbreviations

from .. import cache
from .. import git
from ..config import get_user_config
from ..context import create_context
from ..context import load_context
from ..types import StrMapping


def _ensure_branch_exists(repository: git.Repository, branch: str) -> None:
    try:
        repository.rev_parse(branch, verify=True, quiet=True)
    except git.Error:
        (firstref,) = repository.rev_list(max_count=1, max_parents=0)
        repository.branch(branch, firstref)


def update(
    extra_context: StrMapping,
    *,
    interactive: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[Path] = None,
    config_file: Optional[Path] = None,
    default_config: bool = False,
) -> None:
    """Update a project from a Cookiecutter template."""
    config = get_user_config(config_file=config_file, default_config=default_config)
    instance = git.Repository()
    _ensure_branch_exists(instance, "template")
    previous_context_file = Path(".cookiecutter.json")
    previous_context = load_context(previous_context_file, default={})
    extra_context = {**previous_context, **extra_context}
    template = extra_context["_template"]
    template = expand_abbreviations(
        template=template, abbreviations=config.abbreviations
    )
    entry = cache.Entry(template, directory=directory, revision=checkout)

    with entry.checkout() as repo_dir:
        context_file = repo_dir / "cookiecutter.json"
        current_context = load_context(context_file)
        if not interactive:
            interactive = bool(current_context.keys() - previous_context.keys())
        context = create_context(
            context_file,
            template=template,
            extra_context=extra_context,
            no_input=not interactive,
            default_context=config.default_context,
        )
        entry.dump_context(context)

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
            project.commit(message=f"Update template to {entry.describe}")
