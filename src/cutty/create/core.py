"""Create a project."""
from pathlib import Path
from typing import Optional

from cookiecutter import exceptions
from cookiecutter.generate import generate_files
from cookiecutter.repository import expand_abbreviations

from .. import cache
from .. import config as _config
from ..context import create_context
from ..types import StrMapping


def create(
    template: str,
    extra_context: StrMapping,
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

    config = _config.load(config_file=config_file, default_config=default_config)
    template = expand_abbreviations(
        template=template, abbreviations=config.abbreviations
    )
    entry = cache.Entry(template, directory=directory, revision=checkout)
    with entry.checkout() as repo_dir:
        if replay:
            context = entry.load_context()
        else:
            context_file = repo_dir / "cookiecutter.json"
            context = create_context(
                context_file,
                template=template,
                extra_context=extra_context,
                no_input=no_input,
                default_context=config.default_context,
            )
            entry.dump_context(context)

        generate_files(
            repo_dir=str(repo_dir),
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=output_dir,
        )
