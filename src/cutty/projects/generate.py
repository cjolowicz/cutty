"""Generating projects from templates."""
import pathlib
from collections.abc import Sequence

from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.projects.generator import ProjectGenerator
from cutty.projects.store import storeproject
from cutty.projects.template import Template
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.domain.bindings import Binding


def generate(
    template: Template,
    outputdir: pathlib.Path,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    fileexists: FileExistsPolicy,
    outputdirisproject: bool,
    createconfigfile: bool,
) -> pathlib.Path:
    """Generate a project from a project template."""
    generator = ProjectGenerator.create(template)

    bindings = bindcookiecuttervariables(
        generator.variables,
        generator.renderer,
        interactive=not no_input,
        bindings=extrabindings,
    )

    project = generator.generate(bindings)

    if createconfigfile:
        project = generator.addconfig(project, bindings)

    return storeproject(
        project,
        outputdir,
        outputdirisproject,
        fileexists,
    )
