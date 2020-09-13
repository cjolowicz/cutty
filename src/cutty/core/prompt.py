"""Prompt."""
import json
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import click


def ask(name: str, *, default: Any) -> Any:
    """Prompt for name and return the entered value or given default."""
    return click.prompt(name, default=default)


def ask_choice(name: str, *, values: List[Any]) -> Any:
    """Prompt to choose from several values for the given name."""
    if not values:
        raise ValueError

    choices = {str(number): value for number, value in enumerate(values, 1)}
    numbers = choices.keys()
    prompt = "\n".join(
        [
            f"Select {name}:",
            *[f"{number} - {value}" for number, value in choices.items()],
            "Choose from {}".format(", ".join(numbers)),
        ]
    )
    choice = click.prompt(
        prompt, type=click.Choice(numbers), default="1", show_choices=False
    )

    return choices[choice]


def ask_json_dict(name: str, *, default: Dict[str, Any]) -> Dict[str, Any]:
    """Prompt to provide a dictionary of data."""

    def load_json_dict(value: Optional[str]) -> Any:
        """Load entered value as a JSON dict."""
        assert value is not None  # noqa: S101
        try:
            result = json.loads(value)
        except Exception:
            raise click.UsageError("Unable to decode to JSON.")

        if not isinstance(result, dict):
            raise click.UsageError("Requires JSON dict.")

        return result

    value = click.prompt(
        name, default="default", type=click.STRING, value_proc=load_json_dict
    )

    if value == "default":
        return default

    return cast(Dict[str, Any], value)
