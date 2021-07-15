"""Update a project with changes from its Cookiecutter template."""
import json
from pathlib import Path

from cutty.services.create import create


def getprojecttemplate(projectdir: Path) -> str:
    """Return the location of the project template."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    result: str = data["_template"]
    return result


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    template = getprojecttemplate(Path.cwd())
    create(
        template, no_input=True, outputdir=Path.cwd().parent, overwrite_if_exists=True
    )
