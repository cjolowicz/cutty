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


def valid_hook(path: Path, hook_name: str) -> bool:
    """Determine if a hook file is valid."""
    matching_hook = path.stem == hook_name
    supported_hook = path.stem in _HOOKS
    backup_file = path.name.endswith("~")

    return matching_hook and supported_hook and not backup_file


def find_hook(hook_name: str) -> Optional[Path]:
    """Return the absolute path of the hook script, or None."""
    if _HOOKS_DIR.is_dir():
        for hook_file in _HOOKS_DIR.iterdir():
            if valid_hook(hook_file, hook_name):
                return hook_file.resolve()

    return None


def run_script(script_path: Path, cwd: Path) -> None:
    """Execute a script from a working directory."""
    if script_path.suffix == ".py":
        script_command = [sys.executable, script_path]
    else:
        script_command = [script_path]

    make_executable(script_path)

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


def run_script_with_context(script_path: Path, cwd: Path, context: StrMapping) -> None:
    """Execute a script after rendering it with Jinja."""
    contents = script_path.read_text()

    with tempfile.NamedTemporaryFile(
        delete=False, mode="wb", suffix=script_path.suffix
    ) as temp:
        env = Environment(context=context, keep_trailing_newline=True)
        template = env.from_string(contents)
        output = template.render(**context)
        temp.write(output.encode("utf-8"))

    run_script(Path(temp.name), cwd)


def run_hook(hook_name: str, project_dir: Path, context: StrMapping) -> None:
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is not None:
        run_script_with_context(script, project_dir, context)
