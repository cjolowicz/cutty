"""Generating projects from templates."""
from collections.abc import Sequence

from cutty.projects.generator import ProjectGenerator
from cutty.projects.project import Project
from cutty.projects.template import Template
from cutty.templates.adapters.cookiecutter.binders import bindcookiecuttervariables
from cutty.templates.domain.bindings import Binding


def generate(
    template: Template,
    *,
    extrabindings: Sequence[Binding],
    no_input: bool,
    createconfigfile: bool = True,
) -> Project:
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

    return project
