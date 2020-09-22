"""Engine."""
from pathlib import Path

from .generate import Generator
from .render import Renderer
from .survey import Survey
from .template import Template


class Engine:
    """Engine."""

    def __init__(
        self, template: Template, *, interactive: bool = True, overwrite: bool = False
    ) -> None:
        """Initialize."""
        self.renderer = Renderer(template)
        self.survey = Survey(template, renderer=self.renderer, interactive=interactive)
        self.generator = Generator(
            template, renderer=self.renderer, overwrite=overwrite
        )

    def generate(self, output_dir: Path) -> None:
        """Generate the project."""
        self.survey.run()
        self.generator.generate(output_dir)
