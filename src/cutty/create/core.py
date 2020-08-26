"""Create a project."""
from pathlib import Path
from typing import Optional

from .. import exceptions
from ..cache import Cache
from ..config import Config
from ..context import override_context
from ..context import Store
from ..generate import generate_files
from ..prompt import prompt_for_config


def create(
    template: str,
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
    if replay and no_input:
        raise exceptions.InvalidModeException(
            "You can not use both replay and no_input at the same time."
        )

    config = Config.load(config_file, ignore_config=default_config)
    template = config.abbreviations.expand(template)

    with Cache.load(template, directory=directory, revision=checkout) as cache:
        if replay:
            context = cache.context.load()
        else:
            context = Store(cache.repository / "cookiecutter.json").load()
            context = override_context(context, config.default_context)
            context = prompt_for_config(context, no_input=no_input)
            context = {**context, "_template": template}
            cache.context.dump(context)

        generate_files(
            repo_dir=cache.repository,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=Path(output_dir),
        )
