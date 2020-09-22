"""Generate."""
import contextlib
import fnmatch
import shutil
from pathlib import Path

from . import exceptions
from .hooks import HookManager
from .render import Renderer
from .template import Template
from .utils import on_raise
from .utils import rmtree


def _copy_directory(source: Path, target: Path) -> None:
    shutil.copytree(source, target)


def _copy_file(source: Path, target: Path) -> None:
    shutil.copyfile(source, target)
    shutil.copymode(source, target)


class Generator:
    """Generator."""

    def __init__(self, template: Template, *, renderer: Renderer) -> None:
        """Initialize."""
        self.template = template
        self.renderer = renderer
        self.hooks = HookManager(template=template, renderer=renderer)

    def generate(self, output_dir: Path, overwrite: bool = False) -> None:
        """Generate project."""
        with exceptions.PathRenderError(self.template.root):
            target_dir = output_dir / self.renderer.render(self.template.root.name)

        if target_dir.exists() and not overwrite:
            raise exceptions.ProjectDirectoryExists(target_dir)

        cleanup = (
            on_raise(rmtree, target_dir)
            if not target_dir.exists()
            else contextlib.nullcontext()
        )

        with exceptions.ProjectGenerationFailed():
            with cleanup:
                self.hooks.pre_generate(cwd=target_dir)
                self._generate_directory(self.template.root, target_dir)
                self.hooks.post_generate(cwd=target_dir)

    def _generate_directory(self, source_dir: Path, target_dir: Path) -> None:
        if self._is_copy_only(source_dir):
            _copy_directory(source_dir, target_dir)
        else:
            self._render_directory(source_dir, target_dir)

    def _generate_file(self, source: Path, target: Path) -> None:
        if self._is_copy_only(source):
            _copy_file(source, target)
        else:
            self._render_file(source, target)

    def _render_directory(self, source_dir: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)

        for source in source_dir.iterdir():
            with exceptions.PathRenderError(source):
                target = target_dir / self.renderer.render(source.name)

            if source.is_dir():
                self._generate_directory(source, target)
            else:
                self._generate_file(source, target)

    def _render_file(self, source: Path, target: Path) -> None:
        with exceptions.ContentRenderError(source):
            text = self.renderer.render_path(source)

        target.write_text(text)
        shutil.copymode(source, target)

    def _is_copy_only(self, path: Path) -> bool:
        path = path.relative_to(self.template.root)
        return any(
            fnmatch.fnmatch(str(path), pattern)
            for pattern in self.template.variables.copy_without_render
        )
