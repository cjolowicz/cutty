"""Update a project."""
from pathlib import Path
from typing import Optional

from .. import git
from ..cache import Cache
from ..config import Config
from ..context import override_context
from ..context import Store
from ..generate import generate_files
from ..prompt import prompt_for_config


def _ensure_branch_exists(repository: git.Repository, branch: str) -> None:
    try:
        repository.rev_parse(branch, verify=True, quiet=True)
    except git.Error:
        (firstref,) = repository.rev_list(max_count=1, max_parents=0)
        repository.branch(branch, firstref)


def update(
    *,
    interactive: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Update a project from a Cookiecutter template."""
    config = Config.load(config_file)
    previous_context = Store(Path(".cookiecutter.json")).load()
    template = previous_context["_template"]
    template = config.abbreviations.expand(template)

    with Cache.load(template, directory=directory, revision=checkout) as cache:
        context = Store(cache.repository / "cookiecutter.json").load()
        if not interactive:
            interactive = bool(context.keys() - previous_context.keys())
        context = override_context(context, previous_context)
        context = prompt_for_config(context, no_input=not interactive)
        context = {**context, "_template": template}

        instance = git.Repository()
        project_path = instance.path / ".git" / "cookiecutter" / instance.path.name
        _ensure_branch_exists(instance, "template")

        with instance.worktree(
            project_path, "template", checkout=False, force_remove=True
        ) as project:
            generate_files(
                repo_dir=cache.repository,
                context=context,
                overwrite_if_exists=True,
                output_dir=project.path.parent,
            )
            project.add(all=True)
            project.commit(message=f"Update template to {cache.version}")
