"""Unit tests for cutty.domain.templates."""
from cutty.domain.render import Renderer
from cutty.domain.templates import Template
from cutty.domain.templates import TemplateConfig


def test_template(render: Renderer) -> None:
    """It can be rendered."""
    config = TemplateConfig(variables=(), settings=())
    Template(config=config, files=(), renderer=render)
