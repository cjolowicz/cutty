"""Update a project with changes from its Cookiecutter template."""
import json
from pathlib import Path


def getprojecttemplate(projectdir: Path) -> str:
    """Return the location of the project template."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    return data["_template"]


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
