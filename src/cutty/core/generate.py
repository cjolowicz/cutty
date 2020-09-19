"""Generate."""
import contextlib
import fnmatch
import shutil
from pathlib import Path

from . import exceptions
from .hooks import HookManager
from .render import Renderer
from .template import Template
from .utils import OnRaise
from .utils import rmtree


class Generator:
    """Generator."""

    def __init__(self, template: Template, *, renderer: Renderer) -> None:
        """Initialize."""
        self.template = template
        self.renderer = renderer
        self.hooks = HookManager(template=template, renderer=renderer)

    def generate(self, output_dir: Path, overwrite: bool = False) -> None:
        """Generate project."""
        with exceptions.PathRenderError(
            self.template.root.relative_to(self.template.repository)
        ):
            target_dir = output_dir / self.renderer.render(self.template.root.name)

        if target_dir.exists() and not overwrite:
            raise exceptions.ProjectDirectoryExists(target_dir)

        cleanup = (
            OnRaise(rmtree, target_dir)
            if not target_dir.exists()
            else contextlib.nullcontext()
        )

        with cleanup:
            with self.hooks.run_hooks(cwd=target_dir):
                self._generate_directory(self.template.root, target_dir)

    def _generate_directory(self, source_dir: Path, target_dir: Path) -> None:
        if self._is_copy_only(source_dir):
            shutil.copytree(source_dir, target_dir)
            return

        target_dir.mkdir(parents=True, exist_ok=True)

        for source in source_dir.iterdir():
            with exceptions.PathRenderError(
                source.relative_to(self.template.repository)
            ):
                target = target_dir / self.renderer.render(source.name)

            if source.is_dir():
                self._generate_directory(source, target)
            else:
                self._generate_file(source, target)

    def _generate_file(self, source: Path, target: Path) -> None:
        if self._is_copy_only(source):
            shutil.copyfile(source, target)
        else:
            with exceptions.ContentRenderError(
                source.relative_to(self.template.repository)
            ):
                text = self.renderer.render_path(source)

            target.write_text(text)

        shutil.copymode(source, target)

    def _is_copy_only(self, path: Path) -> bool:
        return any(
            fnmatch.fnmatch(str(path), pattern)
            for pattern in self.template.copy_without_render
        )
