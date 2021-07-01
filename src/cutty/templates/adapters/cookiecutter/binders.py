"""Binding variables in Cookiecutter templates."""
from collections.abc import Sequence

from cutty.templates.adapters.cookiecutter.prompts import prompt
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import Binder
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
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
    binder: Binder = prompt if interactive else binddefault
    binder = override(binder, bindings)
    return renderbindwith(binder)(render, variables)
