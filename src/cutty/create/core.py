"""Create a project."""
import logging
from pathlib import Path
from typing import Optional
from typing import Tuple

from cookiecutter import exceptions
from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.replay import dump
from cookiecutter.replay import load
from cookiecutter.repository import expand_abbreviations

from .. import cache
from .. import tags


logger = logging.getLogger(__name__)


def create(
    template: str,
    extra_context: Tuple[str, ...],
    *,
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[str],
    replay: bool,
    config_file: Optional[str],
) -> None:
    """Create a project from a Cookiecutter template."""
    if replay and (no_input or extra_context):
        raise exceptions.InvalidModeException(
            "You can not use both replay and no_input or extra_context "
            "at the same time."
        )

    config = get_user_config(config_file=config_file)
    template = expand_abbreviations(
        template=template, abbreviations=config["abbreviations"]
    )
    repository = cache.repository(template)
    ref = checkout if checkout is not None else tags.find_latest(repository)
    with cache.worktree(template, ref) as worktree:
        repo_dir = (
            worktree.path if directory is None else worktree.path / Path(directory)
        )
        repo_hash = cache.get_repository_hash(
            template, directory=Path(directory) if directory is not None else None
        )

        if replay:
            context = load(config["replay_dir"], repo_hash)
        else:
            context_file = repo_dir / "cookiecutter.json"

            logger.debug("context_file is %s", context_file)

            context = generate_context(
                context_file=context_file,
                default_context=config["default_context"],
                extra_context=extra_context,
            )
            context["cookiecutter"] = prompt_for_config(context, no_input)
            context["cookiecutter"]["_template"] = template

            dump(config["replay_dir"], repo_hash, context)

        generate_files(repo_dir=str(repo_dir), context=context)
