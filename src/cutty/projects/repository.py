"""Project repositories."""
from pathlib import Path

from cutty.projects.common import GenerateProject
from cutty.projects.create import creategitrepository
from cutty.projects.link import linkproject
from cutty.projects.loadtemplate import TemplateMetadata
from cutty.projects.update import abortupdate
from cutty.projects.update import continueupdate
from cutty.projects.update import skipupdate
from cutty.projects.update import updateproject
from cutty.util.git import Repository


class ProjectRepository:
    """Project repository."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    @classmethod
    def create(cls, projectdir: Path, template: TemplateMetadata) -> None:
        """Initialize the git repository for a project."""
        creategitrepository(projectdir, template)

    def update(
        self, generateproject: GenerateProject, template: TemplateMetadata
    ) -> None:
        """Update a project by applying changes between the generated trees."""
        updateproject(self.path, generateproject, template)

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        continueupdate(self.path)

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        skipupdate(self.path)

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        abortupdate(self.path)

    def link(
        self,
        generateproject: GenerateProject,
        template: TemplateMetadata,
    ) -> None:
        """Link a project to a project template."""
        project = Repository.open(self.path)
        linkproject(project, generateproject, template)
