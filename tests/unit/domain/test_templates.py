"""Unit tests for cutty.domain.templates."""
from cutty.domain.files import RenderableFileLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.varspecs import DefaultVariableBuilder


def test_template(renderable_loader: RenderableLoader) -> None:
    """It can be rendered."""
    loader = RenderableFileLoader(renderable_loader)
    template = Template(loader=loader, variables=[], paths=[])
    template.render(DefaultVariableBuilder())
