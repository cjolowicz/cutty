"""Generating projects from the template."""
import fnmatch
import os.path
import shutil
from pathlib import Path

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


def render_directory(
    dirname: str, context: StrMapping, environment: Environment, output_dir: Path
) -> Path:
    """Render name of a directory, return its path."""
    template = environment.from_string(dirname)
    dirname = template.render(**context)
    return Path(os.path.normpath(output_dir / dirname))


def is_copy_only_path(path: str, context: StrMapping) -> bool:
    """Check whether the given `path` should only be copied and not rendered."""
    patterns = context["cookiecutter"].get("_copy_without_render", [])

    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def generate_files(  # noqa: C901
    repo_dir: Path,
    context: StrMapping,
    output_dir: Path,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Path:
    """Render the template to disk."""
    template_dir = find_template(repo_dir)
    environment = Environment(context=context, keep_trailing_newline=True)

    try:
        project_dir = render_directory(
            template_dir.name, context, environment, output_dir
        )
    except UndefinedError as err:
        msg = "Unable to create project directory '{}'".format(template_dir.name)
        raise UndefinedVariableInTemplate(msg, err, context)

    delete_project_on_failure = not project_dir.exists()

    if project_dir.exists() and not overwrite_if_exists:
        msg = 'Error: "{}" directory already exists'.format(project_dir)
        raise OutputDirExistsException(msg)

    project_dir.mkdir(parents=True, exist_ok=True)

    # Use an absolute path. We will chdir to template_dir for Jinja.
    project_dir = project_dir.resolve()

    with chdir(repo_dir):
        try:
            run_hook("pre_gen_project", str(project_dir), context)
        except FailedHookException:
            if delete_project_on_failure:
                rmtree(project_dir)
            raise

    with chdir(template_dir):
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
                try:
                    directory = render_directory(
                        str(unrendered_dir), context, environment, output_dir
                    )
                except UndefinedError as err:
                    if delete_project_on_failure:
                        rmtree(project_dir)
                    _dir = os.path.relpath(str(unrendered_dir), output_dir)
                    msg = "Unable to create directory '{}'".format(_dir)
                    raise UndefinedVariableInTemplate(msg, err, context)

                directory.mkdir(parents=True, exist_ok=True)

            for f in files:
                infile = os.path.normpath(path / f)
                template = environment.from_string(infile)
                outfile = project_dir / template.render(**context)

                if is_copy_only_path(infile, context):
                    shutil.copyfile(infile, outfile)
                    shutil.copymode(infile, outfile)
                    continue
                try:
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
                except UndefinedError as err:
                    if delete_project_on_failure:
                        rmtree(project_dir)
                    msg = "Unable to create file '{}'".format(infile)
                    raise UndefinedVariableInTemplate(msg, err, context)

    with chdir(repo_dir):
        try:
            run_hook("post_gen_project", str(project_dir), context)
        except FailedHookException:
            if delete_project_on_failure:
                rmtree(project_dir)
            raise

    return project_dir
