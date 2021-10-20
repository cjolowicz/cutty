"""Storing projects."""
import pathlib

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filesystems.domain.purepath import PurePath
from cutty.projects.project import Project


def storeproject(
    project: Project,
    outputdir: pathlib.Path,
    outputdirisproject: bool,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> pathlib.Path:
    """Store a project in the output directory."""
    projectdir = outputdir if outputdirisproject else outputdir / project.name
    storeproject2(
        project,
        projectdir,
        outputdirisproject=outputdirisproject,
        fileexists=fileexists,
    )
    return projectdir


def storeproject2(
    project: Project,
    projectdir: pathlib.Path,
    *,
    outputdirisproject: bool,
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
