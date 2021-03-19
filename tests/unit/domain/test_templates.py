"""Unit tests for cutty.domain.templates."""
from cutty.domain.files import renderfiles
from cutty.domain.templates import Template


def test_template() -> None:
    """It can be rendered."""
    template = Template(files=[], variables=[])
    renderfiles(template.files, [])
