"""Replay."""
import json
from pathlib import Path

from .types import StrMapping


def get_file_name(replay_dir: Path, template_name: str) -> Path:
    """Get the name of file."""
    file_name = "{}.json".format(template_name)
    return replay_dir / file_name


def dump(replay_dir: Path, template_name: str, context: StrMapping) -> None:
    """Write json data to file."""
    replay_dir.mkdir(parents=True, exist_ok=True)

    if "cookiecutter" not in context:
        raise ValueError("Context is required to contain a cookiecutter key")

    replay_file = get_file_name(replay_dir, template_name)

    with replay_file.open("w") as outfile:
        json.dump(context, outfile, indent=2)


def load(replay_dir: Path, template_name: str) -> StrMapping:
    """Read json data from file."""
    replay_file = get_file_name(replay_dir, template_name)

    with replay_file.open("r") as infile:
        context = json.load(infile)

    if "cookiecutter" not in context:
        raise ValueError("Context is required to contain a cookiecutter key")

    return context
