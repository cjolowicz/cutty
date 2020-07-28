"""Update a project."""
from pathlib import Path
from typing import Optional

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_files

from .. import cache
from .. import git
from ..context import create_context
from ..context import load_context
from ..types import StrMapping


def update(
    extra_context: StrMapping,
    *,
    interactive: bool = False,
    checkout: Optional[str] = None,
    config_file: Optional[str] = None,
    directory: Optional[Path] = None,
    default_config: bool = False,
) -> None:
    """Update a project from a Cookiecutter template."""
    config = get_user_config(config_file=config_file, default_config=default_config)
    previous_context_file = Path(".cookiecutter.json")
    if previous_context_file.exists():
        previous_context = load_context(previous_context_file)
    else:
        previous_context = {}
    extra_context = {**previous_context, **extra_context}
    template = extra_context["_template"]
    entry = cache.Entry(template, directory=directory, revision=checkout)

    with entry.checkout() as repo_dir:
        context_file = repo_dir / "cookiecutter.json"
        current_context = load_context(context_file)
        if not interactive:
            interactive = bool(set(current_context) - set(previous_context))
        context = create_context(
            context_file,
            template=template,
            extra_context=extra_context,
            no_input=not interactive,
            config=config,
        )
        entry.dump_context(context)

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
            project.commit(message=f"Update template to {entry.describe}")
