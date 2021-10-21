"""Unit tests for cutty.projects.repository."""
from pathlib import Path

import pytest

from cutty.projects.repository import ProjectRepository


def test_build_cleanup(tmp_path: Path) -> None:
    """It does not leak branches on failure."""
    project = tmp_path / "project"
    repository = ProjectRepository.create(project)
    branches = [*repository.project.heads]

    with pytest.raises(Exception, match="boom"):
        with repository.build():
            raise Exception("boom")

    assert branches == [*repository.project.heads]
