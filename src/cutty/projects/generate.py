"""Generating projects from templates."""
from collections.abc import Sequence

from cutty.projects.generator import ProjectGenerator
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.templates.domain.bindvariables import bindvariables
from cutty.variables.binders import binddefault
from cutty.variables.binders import Binder
from cutty.variables.bindings import Binding
from cutty.variables.prompts import createprompt


def generate(
    template: Template,
    bindings: Sequence[Binding] = (),
    /,
    *,
    interactive: bool,
    createconfigfile: bool = True,
) -> Project:
    """Generate a project from a project template."""
    generator = ProjectGenerator.create(template)

    binder: Binder = createprompt() if interactive else binddefault
    bindings = bindvariables(
        generator.variables,
        generator.renderer,
        binder,
        bindings=bindings,
    )

    project = generator.generate(bindings)

    if createconfigfile:
        project = generator.addconfig(project, bindings)

    return project
