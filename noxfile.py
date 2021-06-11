"""Nox sessions."""
import shutil
import sys
import tarfile
from pathlib import Path
from textwrap import dedent

import nox
from nox_poetry import Session
from nox_poetry import session


package = "cutty"
python_versions = ["3.9"]
nox.options.sessions = (
    "pre-commit",
    "safety",
    "mypy",
    "tests",
    "typeguard",
    "xdoctest",
    "docs-build",
)
dependencies = {
    "doc": ["sphinx", "sphinx-click", "sphinx-rtd-theme"],
    "test": ["pytest", "pygments", "pyftpdlib"],
    "lint": [
        "black",
        "darglint",
        "flake8",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-docstrings",
        "flake8-rst-docstrings",
        "pep8-naming",
        "pre-commit",
        "pre-commit-hooks",
        "reorder-python-imports",
    ],
}


def activate_virtualenv_in_precommit_hooks(session: Session) -> None:
    """Activate virtualenv in hooks installed by pre-commit.

    This function patches git hooks installed by pre-commit to activate the
    session's virtual environment. This allows pre-commit to locate hooks in
    that environment when invoked from git.

    Args:
        session: The Session object.
    """
    if session.bin is None:
        return

    virtualenv = session.env.get("VIRTUAL_ENV")
    if virtualenv is None:
        return

    hookdir = Path(".git") / "hooks"
    if not hookdir.is_dir():
        return

    for hook in hookdir.iterdir():
        if hook.name.endswith(".sample") or not hook.is_file():
            continue

        text = hook.read_text()
        bindir = repr(session.bin)[1:-1]  # strip quotes
        if not (
            Path("A") == Path("a") and bindir.lower() in text.lower() or bindir in text
        ):
            continue

        lines = text.splitlines()
        if not (lines[0].startswith("#!") and "python" in lines[0].lower()):
            continue

        header = dedent(
            f"""\
            import os
            os.environ["VIRTUAL_ENV"] = {virtualenv!r}
            os.environ["PATH"] = os.pathsep.join((
                {session.bin!r},
                os.environ.get("PATH", ""),
            ))
            """
        )

        lines.insert(1, header)
        hook.write_text("\n".join(lines))


@session(name="pre-commit", python=python_versions[0])
def precommit(session: Session) -> None:
    """Lint using pre-commit."""
    args = session.posargs or ["run", "--all-files", "--show-diff-on-failure"]
    session.install(*dependencies["lint"])
    session.run("pre-commit", *args)
    if args and args[0] == "install":
        activate_virtualenv_in_precommit_hooks(session)


@session(python=python_versions[0])
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    requirements = session.poetry.export_requirements()
    session.install("safety")
    session.run("safety", "check", f"--file={requirements}", "--bare")


@session(python=python_versions)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or ["src", "tests", "docs/conf.py"]
    session.install(".")
    session.install("mypy", *dependencies["test"], "types-python-slugify")
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    session.install(".")
    session.install("coverage[toml]", *dependencies["test"])
    try:
        session.run("coverage", "run", "--parallel", "-m", "pytest", *session.posargs)
    finally:
        if session.interactive:
            session.notify("coverage", posargs=[])


@session
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs or ["report"]

    session.install("coverage[toml]")

    if not session.posargs and any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")

    session.run("coverage", *args)


def installeditable(session: Session) -> None:
    """Install the package in editable mode."""
    output = session.run_always(
        "poetry", "build", "--format=sdist", external=True, silent=True, stderr=None
    )
    if output is None:
        return

    assert isinstance(output, str)  # noqa: S101

    package = Path("dist") / output.split()[-1]
    targetdir = package.parent / package.name.removesuffix(".tar.gz")

    if targetdir.is_dir():
        # Remove stale files, but never anything outside `dist`.
        targetdir.resolve().relative_to(Path("dist").resolve())
        shutil.rmtree(targetdir)

    with tarfile.open(package) as archive:
        # Exclude pyproject.toml, we use setuptools as the build backend.
        # Exclude src, we provide a symbolic link instead.
        members = [
            member
            for member in archive.getmembers()
            if Path(member.name).parts[1] not in ["pyproject.toml", "src"]
        ]
        archive.extractall(package.parent, members=members)

    (targetdir / "src").symlink_to(Path("src").resolve())
    session.run_always("python", "-m", "pip", "install", "setuptools", silent=True)
    session.install("-e", str(targetdir), silent=True)


@session(python=python_versions[0])
def unittests(session: Session) -> None:
    """Run the unit tests for a specific module."""
    module, *posargs = session.posargs if session.posargs else [""]

    testdir = Path("tests/unit").joinpath(*module.split("."))
    source = f"{package}.{module}" if module else package

    installeditable(session)
    session.install("coverage[toml]", *dependencies["test"])

    try:
        session.run(
            "coverage",
            "run",
            "--parallel",
            f"--source={source}",
            "-m",
            "pytest",
            *posargs,
            str(testdir),
        )
    finally:
        session.run("coverage", "combine")
        session.run("coverage", "report")


@session(python=python_versions)
def typeguard(session: Session) -> None:
    """Runtime type checking using Typeguard."""
    session.install(".")
    session.install("typeguard", *dependencies["test"])
    session.run("pytest", f"--typeguard-packages={package}", *session.posargs)


@session(python=python_versions)
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.install(".")
    session.install("xdoctest[colors]")
    session.run("python", "-m", "xdoctest", package, *args)


@session(name="docs-build", python=python_versions[0])
def docs_build(session: Session) -> None:
    """Build the documentation."""
    args = session.posargs or ["docs", "docs/_build"]
    session.install(".")
    session.install(*dependencies["doc"])

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-build", *args)


@session(python=python_versions[0])
def docs(session: Session) -> None:
    """Build and serve the documentation with live reloading on file changes."""
    args = session.posargs or ["--open-browser", "docs", "docs/_build"]
    session.install(".")
    session.install("sphinx-autobuild", *dependencies["doc"])

    build_dir = Path("docs", "_build")
    if build_dir.exists():
        shutil.rmtree(build_dir)

    session.run("sphinx-autobuild", *args)
