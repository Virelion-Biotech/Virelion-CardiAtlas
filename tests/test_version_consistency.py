import re
from pathlib import Path

import cardiatlas


def test_package_version_matches_pyproject():
    """Regression test: __version__ and pyproject.toml's [project].version drifted
    apart before (0.5.4 vs 0.5.5). Keep them in lockstep.

    Parsed with a small regex rather than tomllib/tomli so this works on
    Python 3.10, which this project still supports and which predates
    tomllib in the standard library, without adding a test dependency.
    """
    root = Path(__file__).resolve().parents[1]
    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
    assert match, "could not find [project].version in pyproject.toml"
    assert cardiatlas.__version__ == match.group(1)
