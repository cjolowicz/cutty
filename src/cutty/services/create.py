"""Create a project from a Cookiecutter template."""
import pathlib
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

import appdirs

from cutty.filestorage.adapters.cookiecutter import CookiecutterHooksObserver
from cutty.filestorage.adapters.disk import DiskFileStorage
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.filestorage.adapters.git import GitRepositoryObserver
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.path import Path
from cutty.repositories.adapters.storage import getdefaultrepositoryprovider
from cutty.templates.adapters.cookiecutter.config import loadconfig
from cutty.templates.adapters.cookiecutter.prompts import prompt
from cutty.templates.adapters.cookiecutter.render import registerrenderers
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.config import Config
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry
from cutty.templates.domain.renderfiles import renderfiles
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
    provider = getdefaultrepositoryprovider(cachedir)
    path = provider(template, revision=checkout)

    if directory is not None:
        path = path.joinpath(*directory.parts)  # pragma: no cover

    binder = override(
        binddefault if no_input else prompt,
        [Binding(key, value) for key, value in extra_context.items()],
    )

    config = loadconfig(template, path)
    renderregistry = registerrenderers(path, config)
    render = createrenderer({**defaultrenderregistry, **renderregistry})
    renderbind = renderbindwith(binder)
    bindings = renderbind(render, config.variables)

    paths = iterpaths(path, config)
    files = renderfiles(paths, render, bindings)
    hookpaths = iterhooks(path)
    hookfiles: Iterable[File] = renderfiles(hookpaths, render, bindings)

    if output_dir is None:
        output_dir = pathlib.Path.cwd()  # pragma: no cover

    storage: FileStorage
    storage = DiskFileStorage(
        output_dir,
        fileexists=fileexistspolicy(overwrite_if_exists, skip_if_file_exists),
    )

    file, files = peek(files)
    if file is not None:  # pragma: no cover
        project = storage.resolve(file.path.parents[-2])
        hookfiles = tuple(hookfiles)
        if hookfiles:
            storage.observers.append(
                CookiecutterHooksObserver(
                    hookfiles=hookfiles, project=project, fileexists=storage.fileexists
                )
            )
        storage.observers.append(GitRepositoryObserver(project=project))

    with storage:
        for file in files:
            storage.add(file)
