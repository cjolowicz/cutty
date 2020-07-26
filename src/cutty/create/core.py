"""Create a project."""
import logging
from pathlib import Path
from textwrap import dedent
from typing import cast
from typing import Optional

from cookiecutter import exceptions
from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
from cookiecutter.replay import dump
from cookiecutter.replay import load
from cookiecutter.repository import expand_abbreviations

from .. import cache
from .. import git
from .. import tags
from ..types import StrMapping


logger = logging.getLogger(__name__)


def _create_context(
    context_file: Path,
    *,
    template: str,
    extra_context: StrMapping,
    no_input: bool,
    config: StrMapping,
) -> StrMapping:
    logger.debug("context_file is %s", context_file)

    context = generate_context(
        context_file=context_file,
        default_context=config["default_context"],
        extra_context=extra_context,
    )
    context["cookiecutter"] = prompt_for_config(context, no_input)
    context["cookiecutter"]["_template"] = template

    return cast(StrMapping, context)


def _create_repository(project: Path, template: str, revision: str) -> None:
    message = f"""\
    Initial project structure

    This project structure was generated from a project template:

    - Template: {template}
    - Revision: {revision}
    """
    repository = (
        git.Repository(project)
        if (project / ".git").is_dir()
        else git.Repository.init(project)
    )
    repository.git("add", ".")
    repository.git("commit", f"--message={dedent(message)}")
    repository.git("branch", "template")


def create(
    template: str,
    extra_context: StrMapping,
    *,
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[str],
    replay: bool,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    output_dir: str,
    config_file: Optional[str],
    default_config: bool,
) -> None:
    """Create a project from a Cookiecutter template."""
    if replay and (no_input or extra_context):
        raise exceptions.InvalidModeException(
            "You can not use both replay and no_input or extra_context "
            "at the same time."
        )

    config = get_user_config(config_file=config_file, default_config=default_config)
    template = expand_abbreviations(
        template=template, abbreviations=config["abbreviations"]
    )
    with cache.checkout(template, revision=checkout) as worktree:
        revision = tags.describe(worktree)
        repo_dir = (
            worktree.path if directory is None else worktree.path / Path(directory)
        )
        repo_hash = cache.repository_hash(
            template, directory=Path(directory) if directory is not None else None
        )

        if replay:
            context = load(config["replay_dir"], repo_hash)
        else:
            context_file = repo_dir / "cookiecutter.json"
            context = _create_context(
                context_file,
                template=template,
                extra_context=extra_context,
                no_input=no_input,
                config=config,
            )
            dump(config["replay_dir"], repo_hash, context)

        project = generate_files(
            repo_dir=str(repo_dir),
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=output_dir,
        )

    _create_repository(Path(project), template, revision)
