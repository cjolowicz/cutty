"""Hooks."""
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


class Hook:
    """Hook."""

    def __init__(self, path: Path, *, template: Template, renderer: Renderer) -> None:
        """Initialize."""
        self.path = path
        self.template = template
        self.renderer = renderer

    def run(self, *, cwd: Path) -> None:
        """Execute the hook from the specified directory."""
        with self.render() as script:
            self.execute(script, cwd=cwd)

    @contextmanager
    def render(self) -> Iterator[Path]:
        """Render the hook."""
        with exceptions.ContentRenderError(
            self.path.relative_to(self.template.repository)
        ):
            text = self.renderer.render_path(self.path)

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / self.path.name
            script.write_text(text)

            make_executable(script)

            yield script

    def execute(self, path: Path, cwd: Path) -> None:
        """Execute a script from a working directory."""
        command = [Path(sys.executable), path] if path.suffix == ".py" else [path]
        shell = sys.platform == "win32"

        with exceptions.HookFailed(self.path.relative_to(self.template.repository)):
            subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602


class HookManager:
    """Hook manager."""

    def __init__(self, *, template: Template, renderer: Renderer) -> None:
        """Initialize."""
        self.template = template
        self.renderer = renderer

    def pre_generate(self, *, cwd: Path) -> None:
        """Run pre-generate hook."""
        self.run("pre_gen_project", cwd=cwd)

    def post_generate(self, *, cwd: Path) -> None:
        """Run post-generate hook."""
        self.run("post_gen_project", cwd=cwd)

    def run(self, hook_name: str, *, cwd: Path) -> None:
        """Try to find and execute a hook from the specified directory."""
        hook = self.find(hook_name)
        if hook is not None:
            hook.run(cwd=cwd)

    def find(self, name: str) -> Optional[Hook]:
        """Return the hook if found, or None."""
        if self.template.hookdir.is_dir():
            for path in self.template.hookdir.iterdir():
                if path.stem == name and not path.name.endswith("~"):
                    return Hook(path, template=self.template, renderer=self.renderer)

        return None
