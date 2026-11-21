"""The gujarati-phonetic-toggle command."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from gujarati_phonetic import __version__
from gujarati_phonetic.tools.cmd import toggle


def test_without_ibus(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without IBus the command explains the error and exits with code 1."""
    # A None module makes its import fail, as on a system without IBus.
    monkeypatch.setitem(sys.modules, "gujarati_phonetic.io.ibus_client", None)
    with pytest.raises(SystemExit) as stop:
        toggle.main([])
    assert stop.value.code == 1
    assert capsys.readouterr().err.startswith("Error: ")


@pytest.mark.parametrize(
    ("language", "summary"),
    [("gujarati", "ગુજરાતી"), ("english", "English")],
)
def test_prints_and_notifies(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    language: str,
    summary: str,
) -> None:
    """The language now on is printed and shown in a notification."""
    shown: list[str] = []

    def toggle_language() -> str:
        return language

    def notify(title: str, body: str) -> None:
        shown.append(title)

    # Fakes of the IBus and notification modules, as on the target system.
    monkeypatch.setitem(
        sys.modules,
        "gujarati_phonetic.io.ibus_client",
        SimpleNamespace(toggle_language=toggle_language),
    )
    monkeypatch.setitem(
        sys.modules,
        "gujarati_phonetic.io.notification",
        SimpleNamespace(notify=notify),
    )
    toggle.main([])
    assert capsys.readouterr().out.strip() == language
    assert shown == [summary]


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    """--version prints the version and exits cleanly."""
    with pytest.raises(SystemExit) as stop:
        toggle.main(["--version"])
    assert stop.value.code == 0
    assert capsys.readouterr().out.strip() == __version__
