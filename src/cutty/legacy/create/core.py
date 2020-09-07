"""Create a project."""
from pathlib import Path
from typing import Optional

from ...common.cache import Cache
from ...common.config import Config
from ...generate import generate_files
from ..context import Context
from ..prompt import prompt_for_config


def create(
    template: str,
    *,
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[Path] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
    output_dir: str = ".",
    config_file: Optional[Path] = None,
) -> None:
    """Create a project from a Cookiecutter template."""
    config = Config.load(config_file)
    template = config.abbreviations.expand(template)

    with Cache.load(template, directory=directory, revision=checkout) as cache:
        context = Context.load(cache.repository / "cookiecutter.json").data
        context = prompt_for_config(context, no_input=no_input)
        context = {**context, "_template": template}

        generate_files(
            repo_dir=cache.repository,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=Path(output_dir),
        )
