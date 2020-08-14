"""Functions for discovering and executing various cookiecutter hooks."""
import errno
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from typing import Optional

from cookiecutter.exceptions import FailedHookException

from .environment import Environment
from .types import StrMapping
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
    command = [sys.executable, path] if path.suffix == ".py" else [path]
    shell = sys.platform == "win32"

    try:
        subprocess.run(command, shell=shell, cwd=cwd, check=True)  # noqa: S602
    except subprocess.CalledProcessError as error:
        raise FailedHookException(
            f"Hook script failed (exit status: {error.returncode})"
        )
    except OSError as error:
        if error.errno == errno.ENOEXEC:
            raise FailedHookException(
                "Hook script failed, might be an empty file or missing a shebang"
            )
        raise FailedHookException(f"Hook script failed (error: {error})")


def render_script(path: Path, context: StrMapping) -> Path:
    """Render a script with Jinja."""
    text = path.read_text()

    with tempfile.NamedTemporaryFile(
        delete=False, mode="wb", suffix=path.suffix
    ) as temp:
        environment = Environment(context=context, keep_trailing_newline=True)
        template = environment.from_string(text)
        text = template.render(**context)
        temp.write(text.encode("utf-8"))

    path = Path(temp.name)

    make_executable(path)

    return path


def run_hook(hook_name: str, project_dir: Path, context: StrMapping) -> None:
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is not None:
        script = render_script(script, context)
        run_script(script, cwd=project_dir)
