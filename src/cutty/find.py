"""Functions for finding Cookiecutter templates and other components."""
import os

from cookiecutter.exceptions import NonTemplatedInputDirException


def find_template(repo_dir: str) -> str:
    """Determine which child directory of `repo_dir` is the project template."""
    for item in os.listdir(repo_dir):
        if "cookiecutter" in item and "{{" in item and "}}" in item:
            return os.path.join(repo_dir, item)
    else:
        raise NonTemplatedInputDirException
