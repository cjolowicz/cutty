"""Hooks."""
from __future__ import annotations

import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import exceptions
from .compat import contextmanager
from .render import Renderer
from .template import Template
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

    def __init__(self, path: Path, *, renderer: Renderer) -> None:
        """Initialize."""
        self.path = path
        self.renderer = renderer

    def run(self, *, cwd: Path) -> None:
        """Execute the hook from the specified directory."""
        with exceptions.ContentRenderError(self.path):
            text = self.renderer.render_path(self.path)

        with exceptions.HookFailed(self.path):
            with create_temporary_script(self.path.name, text) as script:
                execute_script(script, cwd=cwd)


class Hooks:
    """Hooks."""

    @classmethod
    def load(cls, *, template: Template, renderer: Renderer) -> Hooks:
        """Load the hooks."""
        return Hooks(
            pre_gen_project=cls.find(
                "pre_gen_project", template=template, renderer=renderer
            ),
            post_gen_project=cls.find(
                "post_gen_project", template=template, renderer=renderer
            ),
        )

    @classmethod
    def find(
        cls, name: str, *, template: Template, renderer: Renderer
    ) -> Optional[Hook]:
        """Return the hook if found, or None."""
        if template.hookdir.is_dir():
            for path in template.hookdir.iterdir():
                if path.stem == name and not path.name.endswith("~"):
                    return Hook(path, renderer=renderer)

        return None

    def __init__(
        self, *, pre_gen_project: Optional[Hook], post_gen_project: Optional[Hook]
    ) -> None:
        """Initialize."""
        self.pre_gen_project = pre_gen_project
        self.post_gen_project = post_gen_project

    def pre_generate(self, *, cwd: Path) -> None:
        """Run pre-generate hook."""
        if self.pre_gen_project is not None:
            self.pre_gen_project.run(cwd=cwd)

    def post_generate(self, *, cwd: Path) -> None:
        """Run post-generate hook."""
        if self.post_gen_project is not None:
            self.post_gen_project.run(cwd=cwd)
