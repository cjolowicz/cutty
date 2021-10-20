"""Storing projects."""
import pathlib

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.project import Project


def storeproject(
    project: Project,
    projectdir: pathlib.Path,
    *,
    outputdirisproject: bool = True,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> None:
    """Store a project in the output directory."""
    outputdir = projectdir if outputdirisproject else projectdir.parent
    storage = createcookiecutterstorage(
        outputdir, projectdir, fileexists, project.hooks
    )

    with storage:
        for projectfile in project.files:
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)
