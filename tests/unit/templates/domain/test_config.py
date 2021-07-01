"""Unit tests for cutty.templates.domain.config."""
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.templates.adapters.cookiecutter.config import findhooks
from cutty.templates.domain.config import Config
from cutty.templates.domain.variables import Variable


def test_config(variable: Variable) -> None:
    """It can store settings and variables."""
    Config(settings={"a-setting": "value"}, variables=(variable,))


def test_findhooks_none() -> None:
    """It does not yield if there is no hook directory."""
    filesystem = DictFilesystem({"{{ cookiecutter.project }}": {}})
    path = Path(filesystem=filesystem)
    paths = findhooks(path)

    assert next(paths, None) is None


def test_findhooks_paths() -> None:
    """It returns paths to hooks."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = findhooks(path)

    assert next(paths) == path / "hooks" / "pre_gen_project.py"
    assert next(paths, None) is None


def test_findhooks_bogus_hooks() -> None:
    """It ignores hooks with a backup extension."""
    filesystem = DictFilesystem(
        {
            "hooks": {"pre_gen_project.py~": ""},
            "{{ cookiecutter.project }}": {},
        }
    )
    path = Path(filesystem=filesystem)
    paths = findhooks(path)

    assert next(paths, None) is None
