"""Replay."""
import json
import os

from cookiecutter.utils import make_sure_path_exists

from .types import StrMapping


def get_file_name(replay_dir: str, template_name: str) -> str:
    """Get the name of file."""
    file_name = "{}.json".format(template_name)
    return os.path.join(replay_dir, file_name)


def dump(replay_dir: str, template_name: str, context: StrMapping) -> None:
    """Write json data to file."""
    if not make_sure_path_exists(replay_dir):
        raise IOError("Unable to create replay dir at {}".format(replay_dir))

    if "cookiecutter" not in context:
        raise ValueError("Context is required to contain a cookiecutter key")

    replay_file = get_file_name(replay_dir, template_name)

    with open(replay_file, "w") as outfile:
        json.dump(context, outfile, indent=2)


def load(replay_dir: str, template_name: str) -> StrMapping:
    """Read json data from file."""
    replay_file = get_file_name(replay_dir, template_name)

    with open(replay_file, "r") as infile:
        context = json.load(infile)

    if "cookiecutter" not in context:
        raise ValueError("Context is required to contain a cookiecutter key")

    return context
