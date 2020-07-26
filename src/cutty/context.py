"""Helper functions for contexts."""
import logging
from pathlib import Path
from typing import cast

from cookiecutter.generate import generate_context
from cookiecutter.prompt import prompt_for_config

from .types import StrMapping


logger = logging.getLogger(__name__)


def create_context(
    context_file: Path,
    *,
    template: str,
    extra_context: StrMapping,
    no_input: bool,
    config: StrMapping,
) -> StrMapping:
    """Load context from disk."""
    logger.debug("context_file is %s", context_file)

    context = generate_context(
        context_file=context_file,
        default_context=config["default_context"],
        extra_context=extra_context,
    )
    context["cookiecutter"] = prompt_for_config(context, no_input)
    context["cookiecutter"]["_template"] = template

    return cast(StrMapping, context)
