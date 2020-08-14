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
    if path.suffix == ".py":
        script_command = [sys.executable, path]
    else:
        script_command = [path]

    try:
        proc = subprocess.Popen(
            script_command, shell=sys.platform == "win32", cwd=cwd  # noqa: S602
        )
        exit_status = proc.wait()
        if exit_status != 0:
            raise FailedHookException(
                f"Hook script failed (exit status: {exit_status})"
            )
    except OSError as os_error:
        if os_error.errno == errno.ENOEXEC:
            raise FailedHookException(
                "Hook script failed, might be an " "empty file or missing a shebang"
            )
        raise FailedHookException("Hook script failed (error: {})".format(os_error))


def render_script(path: Path, context: StrMapping) -> Path:
    """Render a script with Jinja."""
    contents = path.read_text()

    with tempfile.NamedTemporaryFile(
        delete=False, mode="wb", suffix=path.suffix
    ) as temp:
        env = Environment(context=context, keep_trailing_newline=True)
        template = env.from_string(contents)
        output = template.render(**context)
        temp.write(output.encode("utf-8"))

    path = Path(temp.name)

    make_executable(path)

    return path


def run_hook(hook_name: str, project_dir: Path, context: StrMapping) -> None:
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is not None:
        script = render_script(script, context)
        run_script(script, cwd=project_dir)
