"""What each key press does."""

from __future__ import annotations

import pytest

from gujarati_phonetic.core.keys import KeyAction, classify_key


@pytest.mark.parametrize(
    ("char", "space", "backspace", "ctrl", "alt", "meta", "expected"),
    [
        ("k", False, False, False, False, False, KeyAction.TYPE),
        ("K", False, False, False, False, False, KeyAction.TYPE),
        ("~", False, False, False, False, False, KeyAction.TYPE),
        (" ", True, False, False, False, False, KeyAction.TYPE),
        ("", False, True, False, False, False, KeyAction.BACKSPACE),
        (" ", True, False, True, False, False, KeyAction.TOGGLE),
        (" ", True, False, False, True, False, KeyAction.TOGGLE),
        (" ", True, False, False, False, True, KeyAction.PASS),
        ("c", False, False, True, False, False, KeyAction.PASS),
        ("v", False, False, True, False, False, KeyAction.PASS),
        ("", False, True, True, False, False, KeyAction.PASS),
        ("\r", False, False, False, False, False, KeyAction.PASS),
        ("", False, False, False, False, False, KeyAction.PASS),
        ("é", False, False, False, False, False, KeyAction.PASS),
    ],
)
def test_classify_key(
    char: str,
    space: bool,
    backspace: bool,
    ctrl: bool,
    alt: bool,
    meta: bool,
    expected: KeyAction,
) -> None:
    """Shortcuts pass, Ctrl/Alt+Space switch, printable keys type."""
    assert classify_key(char, space, backspace, ctrl, alt, meta) == expected
