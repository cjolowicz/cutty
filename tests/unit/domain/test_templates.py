"""Unit tests for cutty.domain.templates."""
from cutty.domain.files import loadfiles
from cutty.domain.files import RenderableFileLoader
from cutty.domain.files import renderfiles
from cutty.domain.renderables import RenderableLoader
from cutty.domain.templates import Template


def test_template(
    renderable_loader: RenderableLoader[str],
) -> None:
    """It can be rendered."""
    files = loadfiles([], RenderableFileLoader(renderable_loader))
    template = Template(files=files, variables=[])
    renderfiles(template.files, [])
