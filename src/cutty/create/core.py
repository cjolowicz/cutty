"""Create a project."""
from pathlib import Path
from typing import Optional

from cookiecutter import exceptions
from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_files
from cookiecutter.repository import expand_abbreviations

from .. import cache
from ..context import create_context
from ..types import StrMapping


def create(
    template: str,
    extra_context: StrMapping,
    *,
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[str] = None,
    replay: bool = False,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    output_dir: str = ".",
    config_file: Optional[str] = None,
    default_config: bool = False,
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
        repo_dir = (
            worktree.path if directory is None else worktree.path / Path(directory)
        )
        if replay:
            context = cache.load_context(
                template, directory=Path(directory) if directory is not None else None
            )
        else:
            context_file = repo_dir / "cookiecutter.json"
            context = create_context(
                context_file,
                template=template,
                extra_context=extra_context,
                no_input=no_input,
                config=config,
            )
            cache.dump_context(
                template,
                context,
                directory=Path(directory) if directory is not None else None,
            )

        generate_files(
            repo_dir=str(repo_dir),
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=output_dir,
        )
