"""Generating projects from the template."""
import contextlib
import fnmatch
import os.path
import shutil
from pathlib import Path
from typing import Iterator

from binaryornot.check import is_binary
from cookiecutter.exceptions import FailedHookException
from cookiecutter.exceptions import NonTemplatedInputDirException
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.exceptions import TemplateSyntaxError
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.hooks import run_hook
from jinja2 import FileSystemLoader
from jinja2.exceptions import UndefinedError

from .environment import Environment
from .types import StrMapping
from .utils import chdir
from .utils import rmtree


def find_template(repo_dir: Path) -> Path:
    """Determine which child directory of `repo_dir` is the project template."""
    for item in repo_dir.iterdir():
        if "cookiecutter" in item.name and "{{" in item.name and "}}" in item.name:
            return item
    else:
        raise NonTemplatedInputDirException


def is_copy_only_path(path: str, context: StrMapping) -> bool:
    """Check whether the given `path` should only be copied and not rendered."""
    patterns = context["cookiecutter"].get("_copy_without_render", [])

    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


@contextlib.contextmanager
def handle_undefined_variables(message: str, context: StrMapping) -> Iterator[None]:
    """Re-raise UndefinedError as UndefinedVariableInTemplate."""
    try:
        yield
    except UndefinedError as error:
        raise UndefinedVariableInTemplate(message, error, context)


def _generate_files(  # noqa: C901
    project_dir: Path,
    environment: Environment,
    context: StrMapping,
    output_dir: Path,
    skip_if_file_exists: bool,
) -> None:
    environment.loader = FileSystemLoader(".")

    for root, dirs, files in os.walk("."):
        path = Path(root)

        copy_dirs = []
        render_dirs = []

        for d in dirs:
            d_ = os.path.normpath(path / d)
            if is_copy_only_path(d_, context):
                copy_dirs.append(d)
            else:
                render_dirs.append(d)

        for copy_dir in copy_dirs:
            indir = os.path.normpath(path / copy_dir)
            outdir = os.path.normpath(project_dir / indir)
            shutil.copytree(indir, outdir)

        # Mutate dirs to exclude copied directories from traversal.
        dirs[:] = render_dirs

        for d in dirs:
            unrendered_dir = project_dir / path / d
            _dir = unrendered_dir.relative_to(output_dir)
            with handle_undefined_variables(
                f"Unable to create directory {_dir!r}", context
            ):
                template = environment.from_string(str(unrendered_dir))
                directory = Path(
                    os.path.normpath(output_dir / template.render(**context))
                )

            directory.mkdir(parents=True, exist_ok=True)

        for f in files:
            infile = os.path.normpath(path / f)

            with handle_undefined_variables(
                f"Unable to create file '{infile}'", context
            ):
                template = environment.from_string(infile)
                outfile = project_dir / template.render(**context)

                if is_copy_only_path(infile, context):
                    shutil.copyfile(infile, outfile)
                    shutil.copymode(infile, outfile)
                    continue

                if outfile.is_dir():
                    continue

                if skip_if_file_exists and outfile.exists():
                    continue

                if is_binary(infile):
                    shutil.copyfile(infile, outfile)
                else:
                    try:
                        # https://github.com/pallets/jinja/issues/767
                        template = environment.get_template(Path(infile).as_posix())
                    except TemplateSyntaxError as exception:
                        # Disable translated so that printed exception contains
                        # verbose information about syntax error location.
                        exception.translated = False
                        raise

                    text = template.render(**context)
                    outfile.write_text(text)

                shutil.copymode(infile, outfile)


def generate_files(
    repo_dir: Path,
    context: StrMapping,
    output_dir: Path,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Path:
    """Render the template to disk."""
    template_dir = find_template(repo_dir)
    environment = Environment(context=context, keep_trailing_newline=True)

    with handle_undefined_variables(
        f"Unable to create project directory {template_dir.name!r}", context
    ):
        template = environment.from_string(template_dir.name)
        project_dir = Path(os.path.normpath(output_dir / template.render(**context)))

    delete_project_on_failure = not project_dir.exists()

    if project_dir.exists() and not overwrite_if_exists:
        raise OutputDirExistsException(
            f'Error: "{project_dir}" directory already exists'
        )

    project_dir.mkdir(parents=True, exist_ok=True)

    # Use an absolute path. We will chdir to template_dir for Jinja.
    project_dir = project_dir.resolve()

    try:
        with chdir(repo_dir):
            run_hook("pre_gen_project", str(project_dir), context)

        with chdir(template_dir):
            _generate_files(
                project_dir, context, output_dir, skip_if_file_exists,
            )

        with chdir(repo_dir):
            run_hook("post_gen_project", str(project_dir), context)
    except (FailedHookException, UndefinedVariableInTemplate):
        if delete_project_on_failure:
            rmtree(project_dir)
        raise

    return project_dir
