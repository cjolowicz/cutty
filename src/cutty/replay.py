"""Replay."""
import json
from pathlib import Path

from .types import StrMapping


def dump(replay_dir: Path, template_name: str, context: StrMapping) -> None:
    """Write json data to file."""
    replay_dir.mkdir(parents=True, exist_ok=True)

    replay_file = replay_dir / f"{template_name}.json"

    with replay_file.open("w") as outfile:
        json.dump(context, outfile, indent=2)


def load(replay_dir: Path, template_name: str) -> StrMapping:
    """Read json data from file."""
    replay_file = replay_dir / f"{template_name}.json"

    with replay_file.open("r") as infile:
        context = json.load(infile)

    return context
