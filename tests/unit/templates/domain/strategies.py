"""Hypothesis strategies for cutty.templates.domain."""
from collections.abc import Callable
from typing import Any
from typing import Optional

from hypothesis import strategies

from cutty.templates.domain.variables import Variable


valuetypes = strategies.sampled_from([int, str, dict[str, str]])


@strategies.composite
def values(draw: Callable[..., Any], valuetype: Any = None) -> Any:
    """A strategy that generates values for template variables."""
    if valuetype is None:
        valuetype = draw(valuetypes)

    values = strategies.from_type(valuetype)

    return draw(values)


@strategies.composite
def variables(
    draw: Callable[..., Any],
    valuetype: Any = None,
    choices: Optional[tuple[Any, ...]] = None,
) -> Variable:
    """A strategy that generates template variables."""
    if valuetype is None:
        valuetype = draw(valuetypes)

    values = strategies.from_type(valuetype)

    name = draw(strategies.text())
    description = draw(strategies.text())
    type_ = getattr(valuetype, "__origin__", valuetype)
    default = draw(values)
    if choices is None:
        with_choices = draw(strategies.booleans())
        choices = (default, *draw(strategies.iterables(values))) if with_choices else ()
    interactive = draw(strategies.booleans())

    return Variable(
        name=name,
        description=description,
        type=type_,
        default=default,
        choices=choices,
        interactive=interactive,
    )
