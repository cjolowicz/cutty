"""Create a project."""
from pathlib import Path
from typing import Optional

from .. import exceptions
from ..cache import Cache
from ..config import Config
from ..context import create_context
from ..context import dump
from ..context import load
from ..generate import generate_files
from ..types import Context


def create(
    template: str,
    extra_context: Context,
    *,
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[Path] = None,
    replay: bool = False,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    output_dir: str = ".",
    config_file: Optional[Path] = None,
    default_config: bool = False,
) -> None:
    """Create a project from a Cookiecutter template."""
    if replay and (no_input or extra_context):
        raise exceptions.InvalidModeException(
            "You can not use both replay and no_input or extra_context "
            "at the same time."
        )

    config = Config.load(config_file, ignore_config=default_config)
    template = config.abbreviations.expand(template)

    with Cache.load(template, directory=directory, revision=checkout) as cache:
        if replay:
            context = load(cache.context)
        else:
            context_file = cache.repository / "cookiecutter.json"
            context = create_context(
                context_file,
                template=template,
                extra_context=extra_context,
                no_input=no_input,
                default_context=config.default_context,
            )
            dump(cache.context, context)

        generate_files(
            repo_dir=cache.repository,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=Path(output_dir),
        )
