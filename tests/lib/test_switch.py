"""Tests of the language switch."""

from __future__ import annotations

from gujarati_phonetic.models.switch import LanguageSwitch


def test_starts_in_gujarati_and_flips() -> None:
    """Gujarati first, then each flip gives the other language."""
    switch = LanguageSwitch()
    assert switch.gujarati
    assert not switch.flip()
    assert not switch.gujarati
    assert switch.flip()
    assert switch.gujarati
