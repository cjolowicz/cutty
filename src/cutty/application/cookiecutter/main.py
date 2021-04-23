"""Main entry point for the Cookiecutter compatibility layer."""
import functools
import pathlib
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

import appdirs

from cutty.application.cookiecutter.config import loadconfig
from cutty.application.cookiecutter.files import CookiecutterFileStorage
from cutty.application.cookiecutter.paths import iterpaths
from cutty.application.cookiecutter.prompts import prompt
from cutty.application.cookiecutter.render import isbinary
from cutty.application.cookiecutter.render import iscopyonly
from cutty.application.cookiecutter.render import registerrenderers
from cutty.repositories.adapters.registry import defaultproviderregistry
from cutty.repositories.adapters.storage import asproviderstore
from cutty.repositories.adapters.storage import RepositoryStorage
from cutty.repositories.domain.providers import repositoryprovider
from cutty.repositories.domain.urls import parseurl
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import override
from cutty.templates.domain.binders import renderbindwith
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.generate import generatefiles
from cutty.templates.domain.render import createrenderer
from cutty.templates.domain.render import defaultrenderregistry


def main(
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
    # Hooks:
    # - providerstore    [options]
    # - providerregistry [options]
    # - templateconfig   [options, path]
    # - filestore        [options, path, templateconfig]
    # - renderbind       [options, path, templateconfig] (e.g. GUI)
    # - binder           [options, path, templateconfig]
    # - rendererregistry [options, path, templateconfig]
    # - iterpaths        [options, path, templateconfig]
    # - norender         [options, path, templateconfig]
    repositorystorage = RepositoryStorage(pathlib.Path(appdirs.user_cache_dir("cutty")))
    provider = repositoryprovider(
        defaultproviderregistry, asproviderstore(repositorystorage)
    )

    storage = CookiecutterFileStorage(
        pathlib.Path.cwd() if output_dir is None else output_dir,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    )

    binder = binddefault if no_input else prompt
    if extra_context:
        binder = override(
            binder, [Binding(key, value) for key, value in extra_context.items()]
        )
    renderbind = renderbindwith(binder)

    url = parseurl(template)
    path = provider(url, revision=checkout)

    if directory is not None:
        path = path.joinpath(*directory.parts)  # pragma: no cover

    config = loadconfig(template, path)
    renderregistry = registerrenderers(path, config)
    render = createrenderer({**defaultrenderregistry, **renderregistry})
    bindings = renderbind(render, config.variables)

    storage.store(
        file
        for path in iterpaths(path, config)
        for file in generatefiles(
            path, render, bindings, norender=[iscopyonly(config), isbinary]
        )
    )
