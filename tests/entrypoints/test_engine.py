"""The gujarati-phonetic-engine command."""

from __future__ import annotations

from pathlib import Path

import pytest

from gujarati_phonetic import __version__
from gujarati_phonetic.tools.cmd import engine


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """--version prints the version and exits cleanly."""
    with pytest.raises(SystemExit) as stop:
        engine.main(["--version"])
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == __version__


def test_bad_layout_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A broken layout file gives an error message and exit code 1."""
    broken = tmp_path / "gu_phone.json"
    broken.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(engine, "default_layout_file", lambda: broken)
    with pytest.raises(SystemExit) as stop:
        engine.main(["--ibus"])
    assert stop.value.code == 1
    assert capsys.readouterr().err.startswith("Error: ")
