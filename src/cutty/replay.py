"""Replay."""
import json
from pathlib import Path

from .types import StrMapping


def dump(replay_dir: Path, template_name: str, context: StrMapping) -> None:
    """Write json data to file."""
    path = replay_dir / f"{template_name}.json"

    with path.open("w") as io:
        json.dump(context, io, indent=2)


def load(replay_dir: Path, template_name: str) -> StrMapping:
    """Read json data from file."""
    path = replay_dir / f"{template_name}.json"

    with path.open("r") as io:
        context = json.load(io)

    return context
