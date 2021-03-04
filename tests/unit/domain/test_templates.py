"""Unit tests for cutty.domain.templates."""
from cutty.domain.files import RenderableFileLoader
from cutty.domain.renderables import RenderableLoader
from cutty.domain.renderables import RenderableRepository
from cutty.domain.templates import Template
from cutty.domain.varspecs import DefaultVariableBuilder


def test_template(
    renderable_loader: RenderableLoader,
    renderable_repository: RenderableRepository,
) -> None:
    """It can be rendered."""
    loader = RenderableFileLoader(renderable_loader, renderable_repository, paths=[])
    template = Template(files=loader, variables=[])
    template.render(DefaultVariableBuilder())
