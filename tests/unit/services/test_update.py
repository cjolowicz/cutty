"""Unit tests for cutty.services.update."""
import json
from pathlib import Path

from cutty.services.update import getprojecttemplate


def test_getprojecttemplate(tmp_path: Path) -> None:
    """It returns the `_template` key from .cookiecutter.json."""
    template = "https://example.com/repository.git"
    text = json.dumps({"_template": template})
    (tmp_path / ".cookiecutter.json").write_text(text)

    assert template == getprojecttemplate(tmp_path)
