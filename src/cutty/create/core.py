"""Create a project."""
from typing import Tuple

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.repository import expand_abbreviations

from .. import cache
from .. import tags


def create(template: str, extra_context: Tuple[str, ...]) -> None:
    """Create a project from a Cookiecutter template."""
    config = get_user_config()
    template = expand_abbreviations(
        template=template, abbreviations=config["abbreviations"]
    )
    repository = cache.repository(template)
    tag = tags.find_latest(repository)
    with cache.worktree(template, tag) as worktree:
        context_file = worktree.path / "cookiecutter.json"
        context = generate_context(
            context_file=context_file,
            default_context=config["default_context"],
            extra_context=extra_context,
        )
        context["cookiecutter"] = prompt_for_config(context)
        context["cookiecutter"]["_template"] = template
        generate_files(repo_dir=str(worktree.path), context=context)
