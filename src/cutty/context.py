"""Helper functions for contexts."""
import json
import logging
from pathlib import Path
from typing import cast
from typing import Optional

from cookiecutter.generate import generate_context
from cookiecutter.prompt import prompt_for_config

from .types import StrMapping


logger = logging.getLogger(__name__)


def load_context(
    context_file: Path, *, default: Optional[StrMapping] = None
) -> StrMapping:
    """Load context from disk."""
    if default is not None and not context_file.exists():
        return default
    with context_file.open() as io:
        return cast(StrMapping, json.load(io))


def create_context(
    context_file: Path,
    *,
    template: str,
    extra_context: StrMapping,
    no_input: bool,
    default_context: StrMapping,
) -> StrMapping:
    """Load context from disk."""
    logger.debug("context_file is %s", context_file)

    context = generate_context(
        context_file=context_file,
        default_context=default_context,
        extra_context=extra_context,
    )
    context["cookiecutter"] = prompt_for_config(context, no_input)
    context["cookiecutter"]["_template"] = template

    return cast(StrMapping, context)
