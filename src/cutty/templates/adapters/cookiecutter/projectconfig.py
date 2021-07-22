"""Configuration for projects generated from Cookiecutter templates."""
import json
from collections.abc import Iterable

from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.bindings import Binding


def createprojectconfigfile(
    project: PurePath, bindings: Iterable[Binding]
) -> RegularFile:
    """Create a JSON file with the settings and bindings for a project."""
    path = project / ".cookiecutter.json"
    data = {binding.name: binding.value for binding in bindings}
    blob = json.dumps(data).encode()

    return RegularFile(path, blob)
