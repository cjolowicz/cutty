"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
from types import MappingProxyType
from typing import Optional

import appdirs

from cutty.filestorage.adapters.cookiecutter import createcookiecutterstorage
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.observers.cookiecutter import CookiecutterHooksObserver
from cutty.filestorage.adapters.observers.git import GitRepositoryObserver
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.filestorage.domain.observers import observe
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.path import Path
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.templates.adapters.cookiecutter.config import loadconfig
from cutty.templates.adapters.cookiecutter.prompts import prompt
from cutty.templates.adapters.cookiecutter.render import createcookiecutterrenderer
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import Binder
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.renderfiles import renderfiles
from cutty.templates.domain.variables import Variable
from cutty.util.peek import peek


def iterpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            break
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover

    yield template_dir


def iterhooks(path: Path) -> Iterator[Path]:
    """Load hooks in a Cookiecutter template."""
    hooks = {"pre_gen_project", "post_gen_project"}
    hookdir = path / "hooks"
    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~") and path.stem in hooks:
                yield path


def bindvariables(
    variables: Sequence[Variable],
    render: Renderer,
    *,
    extra_context: Mapping[str, str],
    no_input: bool,
) -> Sequence[Binding]:
    """Bind the template variables."""
    binder: Binder = binddefault if no_input else prompt
    bindings = [Binding(key, value) for key, value in extra_context.items()]
    binder = override(binder, bindings)
    return renderbindwith(binder)(render, variables)


def get_project_dir(output_dir: Optional[pathlib.Path], file: File) -> pathlib.Path:
    """Determine the location of the generated project."""
    parent = output_dir if output_dir is not None else pathlib.Path.cwd()
    return parent / file.path.parts[0]


def fileexistspolicy(
    overwrite_if_exists: bool, skip_if_file_exists: bool
) -> FileExistsPolicy:
    """Return the policy for overwriting existing files."""
    return (
        FileExistsPolicy.RAISE
        if not overwrite_if_exists
        else FileExistsPolicy.SKIP
        if skip_if_file_exists
        else FileExistsPolicy.OVERWRITE
    )


def createstorage(
    template_dir: Path,
    project_dir: pathlib.Path,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    hookfiles: Sequence[File],
) -> FileStorage:
    """Create storage for the project files."""
    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    storage: FileStorage = DiskFileStorage(project_dir.parent, fileexists=fileexists)

    observer: Optional[FileStorageObserver] = None

    if hookfiles:  # pragma: no branch
        observer = CookiecutterHooksObserver(
            hookfiles=hookfiles, project=project_dir, fileexists=fileexists
        )

    if observer:  # pragma: no branch
        storage = observe(storage, observer)

    storage = observe(storage, GitRepositoryObserver(project=project_dir))

    return storage


def create(
    template: str,
    *,
    extra_context: Mapping[str, str] = MappingProxyType({}),
    no_input: bool = False,
    checkout: Optional[str] = None,
    output_dir: Optional[pathlib.Path] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> None:
    """Generate a project from a Cookiecutter template."""
    cachedir = pathlib.Path(appdirs.user_cache_dir("cutty"))
    template_dir = getdefaultrepositoryprovider(cachedir)(template, revision=checkout)

    if directory is not None:
        template_dir = template_dir.joinpath(*directory.parts)  # pragma: no cover

    config = loadconfig(template, template_dir)
    render = createcookiecutterrenderer(template_dir, config)
    bindings = bindvariables(
        config.variables, render, extra_context=extra_context, no_input=no_input
    )

    paths = iterpaths(template_dir, config)
    files = renderfiles(paths, render, bindings)
    file, files = peek(files)
    if file is None:  # pragma: no cover
        return

    project_dir = get_project_dir(output_dir, file)
    hookfiles = tuple(renderfiles(iterhooks(template_dir), render, bindings))

    with createcookiecutterstorage(
        template_dir,
        project_dir,
        overwrite_if_exists,
        skip_if_file_exists,
        hookfiles,
    ) as storage:
        for file in files:
            storage.add(file)
