"""The gujarati-phonetic-check command."""

from __future__ import annotations

import sys

import pytest

from gujarati_phonetic import __version__
from gujarati_phonetic.tools.cmd import check


def test_without_ibus(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without IBus the command explains the error and exits with code 1."""
    # A None module makes its import fail, as on a system without IBus.
    monkeypatch.setitem(sys.modules, "gujarati_phonetic.io.ibus_client", None)
    with pytest.raises(SystemExit) as stop:
        check.main(["kem Cho"])
    assert stop.value.code == 1
    assert capsys.readouterr().err.startswith("Error: ")


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """--version prints the version and exits cleanly."""
    with pytest.raises(SystemExit) as stop:
        check.main(["--version"])
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == __version__
