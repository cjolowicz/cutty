"""Loading Cookiecutter variables."""
from typing import Any

from cutty.domain.renderables import Renderable
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import TrivialRenderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


def get_variable_type(value: Any) -> VariableType:
    """Return the appropriate variable type for the value."""
    mapping = {
        type(None): VariableType.NULL,
        bool: VariableType.BOOLEAN,
        float: VariableType.NUMBER,
        str: VariableType.STRING,
        list: VariableType.ARRAY,
        dict: VariableType.OBJECT,
    }

    for value_type, variable_type in mapping.items():
        if isinstance(value, value_type):
            return variable_type

    raise RuntimeError(f"unsupported variable type {type(value)}")  # pragma: no cover


def load_variable(
    loader: RenderableLoader, name: str, value: Any
) -> VariableSpecification[Renderable[Value]]:
    """Load a Cookiecutter variable."""
    if name.startswith("_"):
        return VariableSpecification(
            name,
            name,
            get_variable_type(value),
            TrivialRenderable(value),
            choices=(),
            interactive=False,
        )

    if isinstance(value, list):
        [variable_type] = set(get_variable_type(choice) for choice in value)
        choices = tuple(loader.load(choice) for choice in value)
        return VariableSpecification(
            name,
            name,
            variable_type,
            choices[0],
            choices,
            interactive=True,
        )

    return VariableSpecification(
        name,
        name,
        get_variable_type(value),
        loader.load(value),
        choices=(),
        interactive=True,
    )


def load(
    loader: RenderableLoader, data: dict[str, Any]
) -> list[VariableSpecification[Renderable[Value]]]:
    """Load Cookiecutter variables."""
    return [load_variable(loader, name, value) for name, value in data.items()]
