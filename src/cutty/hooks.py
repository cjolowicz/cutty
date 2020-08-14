"""Functions for discovering and executing various cookiecutter hooks."""
import errno
import io
import os
import subprocess  # noqa: S404
import sys
import tempfile

from cookiecutter import utils
from cookiecutter.exceptions import FailedHookException

from .environment import Environment


_HOOKS = [
    "pre_gen_project",
    "post_gen_project",
]

EXIT_SUCCESS = 0


def valid_hook(hook_file, hook_name):
    """Determine if a hook file is valid."""
    filename = os.path.basename(hook_file)
    basename = os.path.splitext(filename)[0]

    matching_hook = basename == hook_name
    supported_hook = basename in _HOOKS
    backup_file = filename.endswith("~")

    return matching_hook and supported_hook and not backup_file


def find_hook(hook_name, hooks_dir="hooks"):
    """Return a dict of all hook scripts provided.

    Must be called with the project template as the current working directory.
    Dict's key will be the hook/script's name, without extension, while values
    will be the absolute path to the script. Missing scripts will not be
    included in the returned dict.
    """
    if not os.path.isdir(hooks_dir):
        return None

    for hook_file in os.listdir(hooks_dir):
        if valid_hook(hook_file, hook_name):
            return os.path.abspath(os.path.join(hooks_dir, hook_file))

    return None


def run_script(script_path, cwd="."):
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


def run_script_with_context(script_path, cwd, context):
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


def run_hook(hook_name, project_dir, context):
    """Try to find and execute a hook from the specified project directory."""
    script = find_hook(hook_name)
    if script is None:
        return
    run_script_with_context(script, project_dir, context)
