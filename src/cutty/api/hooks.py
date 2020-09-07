"""Hooks."""
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from typing import Iterator
from typing import Optional

from ..common.compat import contextmanager
from ..utils import make_executable
from .renderer import Renderer
from .template import Template


HOOKS = [
    "pre_gen_project",
    "post_gen_project",
]


class HookManager:
    """Hook manager."""

    def __init__(self, *, template: Template, renderer: Renderer) -> None:
        """Initialize."""
        self.root = template.root / "hooks"
        self.renderer = renderer

    @contextmanager
    def run_hooks(self, *, cwd: Path) -> Iterator[None]:
        """Context manager to run pre- and post-generation hooks."""
        self.run("pre_gen_project", cwd=cwd)
        yield
        self.run("post_gen_project", cwd=cwd)

    def run(self, hook_name: str, *, cwd: Path) -> None:
        """Try to find and execute a hook from the specified directory."""
        script = self.find(hook_name)
        if script is not None:
            script = self.render(script)
            self.execute(script, cwd=cwd)

    def find(self, name: str) -> Optional[Path]:
        """Return the absolute path of the hook script, or None."""
        assert name in HOOKS  # noqa: S101

        if self.root.is_dir():
            for path in self.root.iterdir():
                if path.stem == name and not path.name.endswith("~"):
                    return path.resolve()

        return None

    def render(self, path: Path) -> Path:
        """Render a script."""
        text = self.renderer.render_path(path)

        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=path.suffix
        ) as temporary:
            temporary.write(text)

        path = Path(temporary.name)

        make_executable(path)

        return path

    def execute(self, path: Path, cwd: Path) -> None:
        """Execute a script from a working directory."""
        command = [Path(sys.executable), path] if path.suffix == ".py" else [path]
        shell = sys.platform == "win32"

        subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602
