"""Unit tests for cutty.domain.templates."""
from tests.unit.conftest import CreateFileRepository

from cutty.domain.files import RenderableFileLoader
from cutty.domain.files import RenderableFileRepository
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateRenderer
from cutty.domain.varspecs import DefaultVariableBuilder


def test_template(
    renderable_loader: RenderableLoader[str],
    create_file_repository: CreateFileRepository,
) -> None:
    """It can be rendered."""
    repository = RenderableFileRepository(
        create_file_repository([]),
        RenderableFileLoader(renderable_loader),
    )
    template = Template(files=repository, variables=[])
    renderer = TemplateRenderer(builder=DefaultVariableBuilder())
    renderer.render(template)
