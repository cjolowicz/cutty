"""Binding variables in Cookiecutter templates."""
from collections.abc import Sequence

from cutty.templates.adapters.cookiecutter.prompts import prompt
from cutty.templates.domain.binders import bindvariables
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.variables import Variable


def bindcookiecuttervariables(
    variables: Sequence[Variable],
    render: Renderer,
    *,
    interactive: bool,
    bindings: Sequence[Binding],
) -> Sequence[Binding]:
    """Bind the template variables."""
    return bindvariables(
        variables, render, prompt, interactive=interactive, bindings=bindings
    )
