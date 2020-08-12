"""Generating projects from the template."""
import os.path
import shutil
from pathlib import Path

from cookiecutter.exceptions import NonTemplatedInputDirException
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.generate import _run_hook_from_repo_dir
from cookiecutter.generate import generate_file
from cookiecutter.generate import is_copy_only_path
from cookiecutter.generate import render_and_create_dir
from cookiecutter.utils import rmtree
from cookiecutter.utils import work_in
from jinja2 import FileSystemLoader
from jinja2.exceptions import UndefinedError

from .environment import Environment
from .types import StrMapping


def find_template(repo_dir: Path) -> Path:
    """Determine which child directory of `repo_dir` is the project template."""
    for item in repo_dir.iterdir():
        if "cookiecutter" in item.name and "{{" in item.name and "}}" in item.name:
            return item
    else:
        raise NonTemplatedInputDirException


def ensure_dir_is_templated(dirname):
    """Ensure that dirname is a templated directory name."""
    if "{{" in dirname and "}}" in dirname:
        return True
    else:
        raise NonTemplatedInputDirException


def generate_files(  # noqa: C901
    repo_dir: Path,
    context: StrMapping,
    output_dir: Path,
    overwrite_if_exists: bool = False,
    skip_if_file_exists: bool = False,
) -> Path:
    """Render the templates and saves them to files."""
    project_dir: str
    template_dir = find_template(repo_dir)

    ensure_dir_is_templated(template_dir.name)
    env = Environment(context=context, keep_trailing_newline=True)
    try:
        project_dir, output_directory_created = render_and_create_dir(
            template_dir.name, context, str(output_dir), env, overwrite_if_exists
        )
    except UndefinedError as err:
        msg = "Unable to create project directory '{}'".format(template_dir.name)
        raise UndefinedVariableInTemplate(msg, err, context)

    # We want the Jinja path and the OS paths to match. Consequently, we'll:
    #   + CD to the template folder
    #   + Set Jinja's path to '.'
    #
    #  In order to build our files to the correct folder(s), we'll use an
    # absolute path for the target folder (project_dir)

    project_dir = os.path.abspath(project_dir)

    # if we created the output directory, then it's ok to remove it
    # if rendering fails
    delete_project_on_failure = output_directory_created

    _run_hook_from_repo_dir(
        str(repo_dir),
        "pre_gen_project",
        project_dir,
        context,
        delete_project_on_failure,
    )

    with work_in(str(template_dir)):
        env.loader = FileSystemLoader(".")

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
                    render_and_create_dir(
                        unrendered_dir,
                        context,
                        str(output_dir),
                        env,
                        overwrite_if_exists,
                    )
                except UndefinedError as err:
                    if delete_project_on_failure:
                        rmtree(project_dir)
                    _dir = os.path.relpath(unrendered_dir, output_dir)
                    msg = "Unable to create directory '{}'".format(_dir)
                    raise UndefinedVariableInTemplate(msg, err, context)

            for f in files:
                infile = os.path.normpath(os.path.join(root, f))
                if is_copy_only_path(infile, context):
                    outfile_tmpl = env.from_string(infile)
                    outfile_rendered = outfile_tmpl.render(**context)
                    outfile = os.path.join(project_dir, outfile_rendered)
                    shutil.copyfile(infile, outfile)
                    shutil.copymode(infile, outfile)
                    continue
                try:
                    generate_file(
                        project_dir, infile, context, env, skip_if_file_exists
                    )
                except UndefinedError as err:
                    if delete_project_on_failure:
                        rmtree(project_dir)
                    msg = "Unable to create file '{}'".format(infile)
                    raise UndefinedVariableInTemplate(msg, err, context)

    _run_hook_from_repo_dir(
        str(repo_dir),
        "post_gen_project",
        project_dir,
        context,
        delete_project_on_failure,
    )

    return Path(project_dir)
