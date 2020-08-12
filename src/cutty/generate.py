"""Generating projects from the template."""
import os.path
import shutil
from pathlib import Path

from binaryornot.check import is_binary
from cookiecutter.exceptions import FailedHookException
from cookiecutter.exceptions import NonTemplatedInputDirException
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.exceptions import TemplateSyntaxError
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.generate import is_copy_only_path
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


def generate_file(
    project_dir: Path,
    infile: Path,
    context: StrMapping,
    environment: Environment,
    skip_if_file_exists: bool,
) -> None:
    """Render filename of infile as name of outfile, handle infile correctly.

    Dealing with infile appropriately:

        a. If infile is a binary file, copy it over without rendering.
        b. If infile is a text file, render its contents and write the
           rendered infile to outfile.

    Precondition:

        When calling `generate_file()`, the root template dir must be the
        current working directory. Using `utils.work_in()` is the recommended
        way to perform this directory change.
    """
    template = environment.from_string(str(infile))
    outfile = project_dir / template.render(**context)

    if outfile.is_dir():
        return

    if skip_if_file_exists and outfile.exists():
        return

    if is_binary(infile):
        shutil.copyfile(infile, outfile)
    else:
        try:
            # https://github.com/pallets/jinja/issues/767
            template = environment.get_template(infile.as_posix())
        except TemplateSyntaxError as exception:
            # Disable translated so that printed exception contains verbose
            # information about syntax error location
            exception.translated = False
            raise

        text = template.render(**context)
        outfile.write_text(text)

    shutil.copymode(infile, outfile)


def generate_files(  # noqa: C901
    repo_dir: Path,
    context: StrMapping,
    output_dir: Path,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Path:
    """Render the templates and saves them to files."""
    template_dir = find_template(repo_dir)

    environment = Environment(context=context, keep_trailing_newline=True)
    try:
        directory = render_directory(
            template_dir.name, context, environment, output_dir
        )
    except UndefinedError as err:
        msg = "Unable to create project directory '{}'".format(template_dir.name)
        raise UndefinedVariableInTemplate(msg, err, context)

    # If we create the output directory, then it's ok to remove it
    # if rendering fails.
    delete_project_on_failure = not directory.exists()

    if directory.exists() and not overwrite_if_exists:
        msg = 'Error: "{}" directory already exists'.format(directory)
        raise OutputDirExistsException(msg)

    directory.mkdir(parents=True, exist_ok=True)

    # We want the Jinja path and the OS paths to match. Consequently, we'll:
    #   + CD to the template folder
    #   + Set Jinja's path to '.'
    #
    #  In order to build our files to the correct folder(s), we'll use an
    # absolute path for the target folder (project_dir)

    project_dir = Path(os.path.abspath(directory))

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
            # We must separate the two types of dirs into different lists.
            # The reason is that we don't want ``os.walk`` to go through the
            # unrendered directories, since they will just be copied.
            copy_dirs = []
            render_dirs = []

            for d in dirs:
                d_ = os.path.normpath(os.path.join(root, d))
                # We check the full path, because that's how it can be
                # specified in the ``_copy_without_render`` setting, but
                # we store just the dir name
                if is_copy_only_path(d_, context):
                    copy_dirs.append(d)
                else:
                    render_dirs.append(d)

            for copy_dir in copy_dirs:
                indir = os.path.normpath(os.path.join(root, copy_dir))
                outdir = os.path.normpath(os.path.join(project_dir, indir))
                shutil.copytree(indir, outdir)

            # We mutate ``dirs``, because we only want to go through these dirs
            # recursively
            dirs[:] = render_dirs
            for d in dirs:
                unrendered_dir = os.path.join(project_dir, root, d)
                try:
                    directory = render_directory(
                        unrendered_dir, context, environment, output_dir
                    )
                except UndefinedError as err:
                    if delete_project_on_failure:
                        rmtree(project_dir)
                    _dir = os.path.relpath(unrendered_dir, output_dir)
                    msg = "Unable to create directory '{}'".format(_dir)
                    raise UndefinedVariableInTemplate(msg, err, context)

                directory.mkdir(parents=True, exist_ok=True)

            for f in files:
                infile = os.path.normpath(os.path.join(root, f))
                if is_copy_only_path(infile, context):
                    outfile_tmpl = environment.from_string(infile)
                    outfile_rendered = outfile_tmpl.render(**context)
                    outfile = os.path.join(project_dir, outfile_rendered)
                    shutil.copyfile(infile, outfile)
                    shutil.copymode(infile, outfile)
                    continue
                try:
                    generate_file(
                        project_dir,
                        Path(infile),
                        context,
                        environment,
                        skip_if_file_exists,
                    )
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
