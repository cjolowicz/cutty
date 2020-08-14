"""Functions for discovering and executing various cookiecutter hooks."""
import errno
import io
import os
import subprocess  # noqa: S404
import sys
import tempfile
from pathlib import Path
from typing import Optional

from cookiecutter import utils
from cookiecutter.exceptions import FailedHookException

from .environment import Environment
from .types import StrMapping

_HOOKS_DIR = "hooks"
_HOOKS = [
    "pre_gen_project",
    "post_gen_project",
]

EXIT_SUCCESS = 0


def valid_hook(hook_file: str, hook_name: str) -> bool:
    """Determine if a hook file is valid."""
    filename = os.path.basename(hook_file)
    basename = os.path.splitext(filename)[0]

    matching_hook = basename == hook_name
    supported_hook = basename in _HOOKS
    backup_file = filename.endswith("~")

    return matching_hook and supported_hook and not backup_file


def find_hook(hook_name: str) -> Optional[str]:
    """Return a dict of all hook scripts provided.

    Must be called with the project template as the current working directory.
    Dict's key will be the hook/script's name, without extension, while values
    will be the absolute path to the script. Missing scripts will not be
    included in the returned dict.
    """
    if not os.path.isdir(_HOOKS_DIR):
        return None

    for hook_file in os.listdir(_HOOKS_DIR):
        if valid_hook(hook_file, hook_name):
            return os.path.abspath(os.path.join(_HOOKS_DIR, hook_file))

    return None


def run_script(script_path: str, cwd: str = ".") -> None:
    """Execute a script from a working directory."""
    run_thru_shell = sys.platform.startswith("win")
    if script_path.endswith(".py"):
        script_command = [sys.executable, script_path]
    else:
        script_command = [script_path]

    utils.make_executable(script_path)

    try:
        proc = subprocess.Popen(
            script_command, shell=run_thru_shell, cwd=cwd  # noqa: S602
        )
        exit_status = proc.wait()
        if exit_status != EXIT_SUCCESS:
            raise FailedHookException(
                "Hook script failed (exit status: {})".format(exit_status)
            )
    except OSError as os_error:
        if os_error.errno == errno.ENOEXEC:
            raise FailedHookException(
                "Hook script failed, might be an " "empty file or missing a shebang"
            )
        raise FailedHookException("Hook script failed (error: {})".format(os_error))


def run_script_with_context(script_path: str, cwd: str, context: StrMapping) -> None:
    """Execute a script after rendering it with Jinja."""
    _, extension = os.path.splitext(script_path)

    with io.open(script_path, "r", encoding="utf-8") as file:
        contents = file.read()

    with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix=extension) as temp:
        env = Environment(context=context, keep_trailing_newline=True)
        template = env.from_string(contents)
        output = template.render(**context)
        temp.write(output.encode("utf-8"))

    run_script(temp.name, cwd)


def run_hook(hook_name: str, project_dir: Path, context: StrMapping) -> None:
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is not None:
        run_script_with_context(script, str(project_dir), context)
