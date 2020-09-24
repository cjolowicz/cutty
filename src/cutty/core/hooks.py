"""Hooks."""
from __future__ import annotations

import dataclasses
import subprocess  # noqa: S404
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import exceptions
from .compat import contextmanager
from .render import Renderer
from .utils import make_executable


@contextmanager
def create_temporary_script(filename: str, text: str) -> Iterator[Path]:
    """Create script with given filename and contents, using a temporary directory."""
    with tempfile.TemporaryDirectory() as directory:
        script = Path(directory) / filename
        script.write_text(text)

        make_executable(script)

        yield script


def execute_script(script: Path, *, cwd: Path) -> None:
    """Execute a script from a working directory."""
    command = [Path(sys.executable), script] if script.suffix == ".py" else [script]
    shell = sys.platform == "win32"

    subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


class Hook:
    """Hook."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    def run(self, *, renderer: Renderer, cwd: Path) -> None:
        """Execute the hook from the specified directory."""
        with exceptions.ContentRenderError(self.path):
            text = renderer.render_path(self.path)

        with exceptions.HookFailed(self.path):
            with create_temporary_script(self.path.name, text) as script:
                execute_script(script, cwd=cwd)


@dataclass
class Hooks:
    """Hooks."""

    pre_gen_project: Optional[Hook]
    post_gen_project: Optional[Hook]

    @classmethod
    def load(cls, path: Path) -> Hooks:
        """Load the hooks."""
        return Hooks(*[cls.find(path, field.name) for field in dataclasses.fields(cls)])

    @classmethod
    def find(cls, hookdir: Path, name: str) -> Optional[Hook]:
        """Return the hook if found, or None."""
        if hookdir.is_dir():
            for path in hookdir.iterdir():
                if path.is_file() and path.stem == name and not path.name.endswith("~"):
                    return Hook(path)

        return None

    def pre_generate(self, *, renderer: Renderer, cwd: Path) -> None:
        """Run pre-generate hook."""
        if self.pre_gen_project is not None:
            self.pre_gen_project.run(renderer=renderer, cwd=cwd)

    def post_generate(self, *, renderer: Renderer, cwd: Path) -> None:
        """Run post-generate hook."""
        if self.post_gen_project is not None:
            self.post_gen_project.run(renderer=renderer, cwd=cwd)
