"""Unit tests for cutty.domain.templates."""
from cutty.domain.templates import Template


def test_template() -> None:
    """It has variables and files."""
    template = Template(variables=[], files=[])
    assert template.variables == ()
    assert template.files == ()
