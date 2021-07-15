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


def getprojectcontext(projectdir: Path) -> dict[str, str]:
    """Return the Cookiecutter context of the project."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectdir = Path.cwd()
    template = getprojecttemplate(projectdir)
    context = getprojectcontext(projectdir)
    create(
        template,
        no_input=True,
        outputdir=projectdir.parent,
        overwrite_if_exists=True,
        extra_context=context,
    )
