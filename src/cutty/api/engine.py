"""Engine."""
from pathlib import Path

from .generate import Generator
from .render import Renderer
from .survey import Survey
from .template import Template


class Engine:
    """Engine."""

    def __init__(self, repo_dir: Path, *, location: str) -> None:
        """Initialize."""
        template = Template.load(repo_dir, location=location)
        self.renderer = Renderer(template)
        self.survey = Survey(template.variables)
        self.generator = Generator(template=template, renderer=self.renderer)

    def generate(self, output_dir: Path) -> None:
        """Generate the project."""
        self.survey.run(self.renderer)
        self.generator.generate(output_dir)
