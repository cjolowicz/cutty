"""Unit tests for cutty.application.cookiecutter.main."""
from cutty.application.cookiecutter.main import iterhooks
from cutty.application.cookiecutter.main import iterpaths
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.domain.config import Config


def test_iterpaths_template_directory() -> None:
    """It returns the template directory."""
    config = Config({}, ())
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = iterpaths(path, config)

    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None


def test_iterpaths_other_directories() -> None:
    """It ignores other directories."""
    config = Config({}, ())
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = iterpaths(path, config)

    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None


def test_iterhooks_none() -> None:
    """It does not yield if there is no hook directory."""
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths, None) is None


def test_iterhooks_paths() -> None:
    """It returns paths to hooks."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths) == path / "hooks" / "pre_gen_project.py"
    assert next(paths, None) is None


def test_iterhooks_bogus_hooks() -> None:
    """It ignores hooks with a backup extension."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = iterhooks(path)

    assert next(paths, None) is None
