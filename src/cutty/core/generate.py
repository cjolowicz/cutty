"""Generate."""
import contextlib
import fnmatch
import os.path
import shutil
from pathlib import Path

from . import exceptions
from .hooks import Hooks
from .render import Renderer
from .template import Template
from .utils import on_raise
from .utils import rmtree


class Generator:
    """Generator."""

    def __init__(
        self, template: Template, *, renderer: Renderer, overwrite: bool = False
    ) -> None:
        """Initialize."""
        self.template = template
        self.renderer = renderer
        self.overwrite = overwrite
        self.hooks = Hooks.load(template.hookdir)

    def generate(self, output_dir: Path) -> Path:
        """Generate project."""
        assert self.template.root.is_dir()  # noqa: S101

        with exceptions.PathRenderError(self.template.root):
            target = output_dir / self.renderer.render(self.template.root.name)

        if os.path.lexists(target):
            if not self.overwrite:
                raise exceptions.ProjectDirectoryExists(target)

            if not target.is_dir() or target.is_symlink():
                target.unlink()

            cleanup = contextlib.nullcontext()
        else:
            cleanup = on_raise(rmtree, target)

        with cleanup:
            with exceptions.ProjectGenerationFailed():
                self._render_directory(self.template.root, target, root=True)

        return target

    def _render(self, source: Path, output_dir: Path) -> None:
        with exceptions.PathRenderError(source):
            target = output_dir / self.renderer.render(source.name)

        # If the target exists at this point, we are in overwrite mode. Remove
        # existing files and symlinks, but do not recursively remove directory
        # trees. Unlinking is required to replace symlinks, and to replace
        # regular files by symlinks or directories. For safety, a directory
        # tree is never replaced by a symlink or regular file. Furthermore,
        # generating a project _across_ a symlink is not supported.
        if target.exists() and not target.is_dir() or target.is_symlink():
            target.unlink()

        if source.is_symlink():
            self._render_symlink(source, target)
        elif source.is_dir():
            self._render_directory(source, target)
        else:
            self._render_file(source, target)

    def _render_directory(
        self, source: Path, target: Path, *, root: bool = False
    ) -> None:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copymode(source, target)

        if root:
            self.hooks.pre_generate(renderer=self.renderer, cwd=target)

        for entry in source.iterdir():
            self._render(entry, target)

        if root:
            self.hooks.post_generate(renderer=self.renderer, cwd=target)

    def _render_symlink(self, source: Path, target: Path) -> None:
        source_target = os.readlink(source)
        with exceptions.SymlinkRenderError(source, source_target):
            target_target = self.renderer.render(source_target)

        target.symlink_to(target_target)
        shutil.copymode(source, target, follow_symlinks=False)

    def _render_file(self, source: Path, target: Path) -> None:
        with exceptions.ContentRenderError(source):
            text = (
                self.renderer.render_path(source)
                if not self._is_copy_only(source)
                else source.read_text()
            )

        target.write_text(text)
        shutil.copymode(source, target)

    def _is_copy_only(self, source: Path) -> bool:
        source = source.relative_to(self.template.root)
        return any(
            fnmatch.fnmatch(str(path), pattern)
            for path in [source, *source.parents]
            for pattern in self.template.variables.copy_without_render
        )
