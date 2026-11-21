"""Typing the composition straight into the document, as key presses.

For applications that drop the text of input methods (ONLYOFFICE): the word
being typed is real text in the document, and each change is made with
Backspace presses and the new characters.
"""

from __future__ import annotations


def needs_key_presses(client: str) -> bool:
    """Tell whether an IBus client drops the text of input methods.

    ONLYOFFICE's documents are a Chromium view (CEF) that IBus knows as
    "gtk3-im:DesktopEditors"; it shows the underlined composition but drops
    the committed text. The toolkit part before ":" is not checked, so that a
    new toolkit in an ONLYOFFICE update keeps the key presses.

    Args:
        client: The client name IBus gives on focus.

    Returns:
        Whether the client gets the text as key presses.
    """
    _, _, program = client.rpartition(":")
    return program == "DesktopEditors"


def screen_edit(shown: str, text: str) -> tuple[int, str]:
    """Find the key presses that turn the text on screen into new text.

    Args:
        shown: The text typed on screen so far, that may still change.
        text: The text that must replace it.

    Returns:
        The number of Backspace presses, then the characters to type.
    """
    common = 0
    for old, new in zip(shown, text):
        if old != new:
            break
        common += 1
    return len(shown) - common, text[common:]


def keysym_for(char: str) -> int:
    """Return the X key symbol that types a character.

    Args:
        char: One character.

    Returns:
        The key symbol: the code point for Latin-1, else the Unicode key symbol.
    """
    # Latin-1 key symbols are the code points; the others are the code point
    # plus 0x01000000 (X11 keysymdef.h).
    code = ord(char)
    keysym = code if code < 0x100 else 0x01000000 + code
    return keysym
