"""Update a project."""
from pathlib import Path
from typing import Optional

from ..common import git
from ..common.cache import Cache
from ..common.config import Config
from .engine import Engine
from .template import Config as TemplateConfig
from .template import Template


def _ensure_branch_exists(repository: git.Repository, branch: str) -> None:
    try:
        repository.rev_parse(branch, verify=True, quiet=True)
    except git.Error:
        (firstref,) = repository.rev_list(max_count=1, max_parents=0)
        repository.branch(branch, firstref)


def update(
    *,
    interactive: bool = False,
    revision: Optional[str] = None,
    directory: Optional[Path] = None,
    config_file: Optional[Path] = None,
) -> None:
    """Update a project from a Cookiecutter template."""
    instance = git.Repository()
    previous_template = TemplateConfig.load(instance.path / ".cookiecutter.json")

    config = Config.load(config_file)
    location = config.abbreviations.expand(previous_template.location)

    _ensure_branch_exists(instance, "template")

    with instance.worktree(
        instance.path / ".git" / "cutty" / instance.path.name,
        "template",
        checkout=False,
        force_remove=True,
    ) as project:
        with Cache.load(location, directory=directory, revision=revision) as cache:
            template = Template.load(
                cache.repository, location=location, overrides=previous_template,
            )
            engine = Engine(template, interactive=interactive)
            engine.generate(project.path.parent)

            project.add(all=True)
            project.commit(message=f"Update template to {cache.version}")

            commit = project.rev_parse("HEAD", verify=False)
            instance.cherrypick(commit)
