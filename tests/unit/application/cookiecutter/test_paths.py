"""Unit tests for cutty.application.cookiecutter.paths."""
from cutty.application.cookiecutter.paths import loadpaths
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.domain.config import Config


def test_loadpaths_hooks() -> None:
    """It prepends hooks to the path sequence."""
    config = Config({}, ())
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = loadpaths(path, config)

    assert next(paths) == path / "hooks" / "pre_gen_project.py"
    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None


def test_loadpaths_bogus_hooks() -> None:
    """It ignores hooks with a backup extension."""
    config = Config({}, ())
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = loadpaths(path, config)

    assert next(paths) == path / "{{ cookiecutter.project }}"
    assert next(paths, None) is None
