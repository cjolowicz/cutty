"""Unit tests for cutty.application.cookiecutter.hooks."""
from cutty.application.cookiecutter.hooks import iterhooks
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path


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
