"""Unit tests."""
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.projects.cookiecutter import findcookiecutterhooks
from cutty.projects.cookiecutter import findcookiecutterpaths
from cutty.rendering.adapters.cookiecutter.render import CookiecutterConfig
from cutty.variables.domain.variables import Variable


def test_config(variable: Variable) -> None:
    """It can store settings and variables."""
    CookiecutterConfig(settings={"a-setting": "value"}, variables=(variable,))


def test_findcookiecutterpaths_template_directory() -> None:
    """It returns the template directory."""
    config = CookiecutterConfig({}, ())
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = findcookiecutterpaths(path, config)

    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None


def test_findcookiecutterpaths_other_directories() -> None:
    """It ignores other directories."""
    config = CookiecutterConfig({}, ())
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = findcookiecutterpaths(path, config)

    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None


def test_findcookiecutterhooks_none() -> None:
    """It does not yield if there is no hook directory."""
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = findcookiecutterhooks(path)

    assert next(paths, None) is None


def test_findcookiecutterhooks_paths() -> None:
    """It returns paths to hooks."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = findcookiecutterhooks(path)

    assert next(paths) == path / "hooks" / "pre_gen_project.py"
    assert next(paths, None) is None


def test_findcookiecutterhooks_bogus_hooks() -> None:
    """It ignores hooks with a backup extension."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = findcookiecutterhooks(path)

    assert next(paths, None) is None
