"""What a key press does, independent of the input method framework."""

from __future__ import annotations

from enum import Enum


class KeyAction(Enum):
    """The handling of one key press."""

    # Switch between Gujarati and English (Ctrl+Space or Alt+Space).
    TOGGLE = "toggle"
    # A character for the phonetic rules.
    TYPE = "type"
    # Backspace while typing Gujarati.
    BACKSPACE = "backspace"
    # Any other key: finish the word and let the application handle the key.
    PASS = "pass"


def classify_key(
    char: str, is_space: bool, is_backspace: bool, ctrl: bool, alt: bool, meta: bool
) -> KeyAction:
    """Decide what a key press does.

    Args:
        char: The character the key types on a US keyboard ("" if none).
        is_space: Whether the key is Space.
        is_backspace: Whether the key is Backspace.
        ctrl: Whether Ctrl is held.
        alt: Whether Alt is held.
        meta: Whether Super, Meta or Hyper (the Search key) is held.

    Returns:
        The action. Shortcuts with Ctrl, Alt or Search pass to the application,
        as on ChromeOS; only Ctrl+Space and Alt+Space are kept for switching.
    """
    match (is_space, is_backspace, ctrl or alt or meta):
        case (True, _, True) if (ctrl or alt) and not meta:
            action = KeyAction.TOGGLE
        case (_, _, True):
            action = KeyAction.PASS
        case (_, True, False):
            action = KeyAction.BACKSPACE
        case (True, _, False):
            action = KeyAction.TYPE
        case _ if len(char) == 1 and " " < char <= "~":
            action = KeyAction.TYPE
        case _:
            action = KeyAction.PASS
    return action
