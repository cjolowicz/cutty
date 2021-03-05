"""Unit tests for cutty.domain.templates."""
from cutty.domain.files import DefaultRenderableFileRepository
from cutty.domain.files import RenderableRepository
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.varspecs import DefaultVariableBuilder


def test_template(
    renderable_loader: RenderableLoader,
    renderable_repository: RenderableRepository,
) -> None:
    """It can be rendered."""
    repository = DefaultRenderableFileRepository(
        renderable_loader, renderable_repository
    )
    template = Template(files=repository, variables=[])
    template.render(DefaultVariableBuilder())
