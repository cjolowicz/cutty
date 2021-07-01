"""Unit tests for cutty.services.create."""
from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path
from cutty.services.create import iterpaths
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
