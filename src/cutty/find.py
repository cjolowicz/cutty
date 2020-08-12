"""Functions for finding Cookiecutter templates and other components."""
import os

from cookiecutter.exceptions import NonTemplatedInputDirException


def find_template(repo_dir: str) -> str:
    """Determine which child directory of `repo_dir` is the project template."""
    repo_dir_contents = os.listdir(repo_dir)

    project_template = None
    for item in repo_dir_contents:
        if "cookiecutter" in item and "{{" in item and "}}" in item:
            project_template = item
            break

    if project_template:
        project_template = os.path.join(repo_dir, project_template)
        return project_template
    else:
        raise NonTemplatedInputDirException
