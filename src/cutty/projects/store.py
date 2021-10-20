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
    return storeproject2(project, projectdir, outputdir, outputdirisproject, fileexists)


def storeproject2(
    project: Project,
    projectdir: pathlib.Path,
    outputdir: pathlib.Path,
    outputdirisproject: bool,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> pathlib.Path:
    """Store a project in the output directory."""
    storage = createcookiecutterstorage(
        outputdir, projectdir, fileexists, project.hooks
    )

    with storage:
        for projectfile in project.files:
            if outputdirisproject:
                path = PurePath(*projectfile.path.parts[1:])
                projectfile = projectfile.withpath(path)

            storage.add(projectfile)

    return projectdir
