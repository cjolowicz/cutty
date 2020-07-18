"""Create a project."""
import logging
from pathlib import Path
from typing import Optional
from typing import Tuple

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.generate import generate_files
from cookiecutter.prompt import prompt_for_config
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
) -> None:
    """Create a project from a Cookiecutter template."""
    config = get_user_config()
    template = expand_abbreviations(
        template=template, abbreviations=config["abbreviations"]
    )
    repository = cache.repository(template)
    ref = checkout if checkout is not None else tags.find_latest(repository)
    with cache.worktree(template, ref) as worktree:
        repo_dir = (
            worktree.path if directory is None else worktree.path / Path(directory)
        )
        context_file = repo_dir / "cookiecutter.json"

        logger.debug("context_file is %s", context_file)

        context = generate_context(
            context_file=context_file,
            default_context=config["default_context"],
            extra_context=extra_context,
        )
        context["cookiecutter"] = prompt_for_config(context, no_input)
        context["cookiecutter"]["_template"] = template
        generate_files(repo_dir=str(repo_dir), context=context)
