"""Generating projects from templates."""
from collections.abc import Sequence

from cutty.projects.generator import ProjectGenerator
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.templates.adapters.questionary.prompts import createprompt
from cutty.templates.domain.binders import bindvariables
from cutty.variables.bindings import Binding


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

    bindings = bindvariables(
        generator.variables,
        generator.renderer,
        createprompt(),
        interactive=interactive,
        bindings=bindings,
    )

    project = generator.generate(bindings)

    if createconfigfile:
        project = generator.addconfig(project, bindings)

    return project
