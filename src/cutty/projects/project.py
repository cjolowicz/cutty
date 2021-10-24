"""Project."""
from __future__ import annotations

import dataclasses
import itertools
from collections.abc import Iterable
from dataclasses import dataclass

from cutty.errors import CuttyError
from cutty.filestorage.domain.files import File
from cutty.projects.template import Template


class EmptyTemplateError(CuttyError):
    """The template contains no project files."""


@dataclass(frozen=True)
class Project:
    """A generated project."""

    template: Template.Metadata
    name: str
    files: Iterable[File]
    hooks: Iterable[File]

    @classmethod
    def create(
        cls,
        template: Template.Metadata,
        files: Iterable[File],
        hooks: Iterable[File],
    ) -> Project:
        """Create a project."""
        files = iter(files)

        try:
            first = next(files)
        except StopIteration:
            raise EmptyTemplateError()

        files = itertools.chain([first], files)
        name = first.path.parts[0]
        return Project(template, name, files, hooks)

    def add(self, file: File) -> Project:
        """Add a project file."""
        return dataclasses.replace(self, files=itertools.chain(self.files, [file]))
