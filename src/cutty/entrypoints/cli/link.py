"""Command-line interface for linking projects to a Cookiecutter template."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.errors import fatal
from cutty.services.link import link as service_link
from cutty.variables.domain.bindings import Binding


@click.command()
@click.argument("template", required=False)
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Directory of the generated project.",
)
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "--template-directory",
    metavar="DIR",
    type=click.Path(path_type=pathlib.Path),
    help=(
        "Directory within the template repository that contains the "
        "cookiecutter.json file."
    ),
)
@fatal
def link(
    template: Optional[str],
    extra_context: dict[str, str],
    non_interactive: bool,
    cwd: Optional[pathlib.Path],
    revision: Optional[str],
    template_directory: Optional[pathlib.Path],
) -> None:
    """Link project to a Cookiecutter template."""
    if cwd is None:
        cwd = pathlib.Path.cwd()

    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    service_link(
        template,
        cwd,
        extrabindings=extrabindings,
        interactive=not non_interactive,
        revision=revision,
        directory=template_directory,
    )
