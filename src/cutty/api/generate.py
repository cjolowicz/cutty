"""Generate."""
import fnmatch
import shutil
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from .hooks import HookManager
from .render import Renderer
from .template import Template


class RemoveTree:
    """Remove a directory tree on exit, unless it already existed."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.stack = ExitStack()
        if not path.exists():
            self.stack.callback(shutil.rmtree, path)

    def __enter__(self) -> Any:
        """Enter the context."""
        self.stack.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context."""
        self.stack.__exit__(*args)

    def cancel(self) -> None:
        """Do not remove the directory tree."""
        self.stack.pop_all()


class Generator:
    """Generator."""

    def __init__(self, *, template: Template, renderer: Renderer) -> None:
        """Initialize."""
        self.template = template
        self.renderer = renderer
        self.hooks = HookManager(template=template, renderer=renderer)

    def generate(self, output_dir: Path) -> None:
        """Generate project."""
        target_dir = output_dir / self.renderer.render(self.template.root.name)
        with RemoveTree(target_dir) as rmtree:
            with self.hooks.run_hooks(cwd=target_dir):
                self._generate_directory(self.template.root, target_dir)
            rmtree.cancel()

    def _generate_directory(self, source_dir: Path, target_dir: Path) -> None:
        if self._is_copy_only(source_dir):
            shutil.copytree(source_dir, target_dir)
            return

        target_dir.mkdir(parents=True, exist_ok=True)
        for source in source_dir.iterdir():
            target = target_dir / self.renderer.render(source.name)
            if source.is_dir():
                self._generate_directory(source, target)
            else:
                self._generate_file(source, target)

    def _generate_file(self, source: Path, target: Path) -> None:
        if self._is_copy_only(source):
            shutil.copyfile(source, target)
        else:
            text = self.renderer.render_path(source)
            target.write_text(text)

        shutil.copymode(source, target)

    def _is_copy_only(self, path: Path) -> bool:
        return any(
            fnmatch.fnmatch(str(path), pattern)
            for pattern in self.template.config.copy_without_render
        )
