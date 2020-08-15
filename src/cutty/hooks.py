"""Functions for discovering and executing various cookiecutter hooks."""
import errno
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from typing import Optional

from . import exceptions
from .environment import Environment
from .types import Context
from .utils import make_executable


_HOOKS_DIR = Path("hooks")
_HOOKS = [
    "pre_gen_project",
    "post_gen_project",
]


def find_hook(name: str) -> Optional[Path]:
    """Return the absolute path of the hook script, or None."""
    if name in _HOOKS and _HOOKS_DIR.is_dir():
        for path in _HOOKS_DIR.iterdir():
            if path.stem == name and not path.name.endswith("~"):
                return path.resolve()

    return None


def run_script(path: Path, cwd: Path) -> None:
    """Execute a script from a working directory."""
    command = [Path(sys.executable), path] if path.suffix == ".py" else [path]
    shell = sys.platform == "win32"

    try:
        subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602
    except subprocess.CalledProcessError as error:
        raise exceptions.FailedHookException(
            f"Hook script failed (exit status: {error.returncode})"
        )
    except OSError as error:
        if error.errno == errno.ENOEXEC:
            raise exceptions.FailedHookException(
                "Hook script failed, might be an empty file or missing a shebang"
            )
        raise exceptions.FailedHookException(f"Hook script failed (error: {error})")


def render_script(path: Path, context: Context) -> Path:
    """Render a script with Jinja."""
    environment = Environment(context=context, keep_trailing_newline=True)
    text = path.read_text()
    template = environment.from_string(text)
    text = template.render(cookiecutter=context)

    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=path.suffix
    ) as temporary:
        temporary.write(text)

    path = Path(temporary.name)

    make_executable(path)

    return path


def run_hook(hook_name: str, project_dir: Path, context: Context) -> None:
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is not None:
        script = render_script(script, context)
        run_script(script, cwd=project_dir)
