"""Unit tests for cutty.templates.domain.config."""
from cutty.templates.domain.config import Config
from cutty.templates.domain.variables import Variable


def test_config(variable: Variable) -> None:
    """It can store settings and variables."""
    Config(settings={"a-setting": "value"}, variables=(variable,))
