"""Tests of the key presses that type the composition into the document."""

from __future__ import annotations

import pytest

from gujarati_phonetic.core.screen import keysym_for, needs_key_presses, screen_edit
from gujarati_phonetic.models.composer import Composer
from gujarati_phonetic.models.parsed_layout import ParsedLayout


@pytest.mark.parametrize(
    ("client", "expected"),
    [
        ("gtk3-im:DesktopEditors", True),
        ("gtk4-im:DesktopEditors", True),
        ("gtk3-im:soffice", False),
        ("QIBusInputContext", False),
        ("fake", False),
        ("", False),
    ],
)
def test_needs_key_presses(client: str, expected: bool) -> None:
    """Only ONLYOFFICE's documents get key presses."""
    assert needs_key_presses(client) == expected


@pytest.mark.parametrize(
    ("shown", "text", "expected"),
    [
        ("", "ક", (0, "ક")),
        ("ક", "કા", (0, "ા")),
        ("કે", "કેમ", (0, "મ")),
        ("સ", "શ", (1, "શ")),
        ("કેમ", "કેમ ", (0, " ")),
        ("કેમ", "", (3, "")),
        ("", "", (0, "")),
    ],
)
def test_screen_edit(shown: str, text: str, expected: tuple[int, str]) -> None:
    """Only the changed end of the text is erased and typed again."""
    assert screen_edit(shown, text) == expected


@pytest.mark.parametrize(
    ("char", "keysym"),
    [(" ", 0x20), ("a", 0x61), ("é", 0xE9), ("ક", 0x1000A95), ("₹", 0x10020B9)],
)
def test_keysym_for(char: str, keysym: int) -> None:
    """Latin-1 keeps its code point; other characters get Unicode key symbols."""
    assert keysym_for(char) == keysym


@pytest.mark.parametrize(
    "keys",
    [
        "kem Cho ",
        "gujaraatii ",
        "vidyArthI ",
        "satya",
        "kemm\b ",
        "sa\b\bshA",
        "k\b\bx",
    ],
)
def test_key_presses_give_the_same_text_as_ibus_text(
    layout: ParsedLayout, keys: str
) -> None:
    """Key presses leave the same text in the document as IBus text."""
    # Simulate a document typed with IBus text (commit and composition), and one
    # typed with the key presses of the engine's key presses mode.
    by_text = _type(Composer(layout), keys, False)
    by_keys = _type(Composer(layout), keys, True)
    assert by_keys == by_text


def _type(composer: Composer, keys: str, key_presses: bool) -> str:
    """Type keys into a simulated document.

    Args:
        composer: A new composer.
        keys: The keys ("\b" for Backspace).
        key_presses: Whether to type the composition as key presses.

    Returns:
        The document, with the composition left at the end.
    """
    document = ""
    shown = ""
    composition = ""
    for key in keys:
        result = composer.type_key(key)
        if not result.handled:
            document = document[:-1] if key == "\b" else f"{document}{key}"
        elif key_presses:
            backspaces, chars = screen_edit(
                shown, f"{result.commit}{result.composition}"
            )
            document = f"{document[: len(document) - backspaces]}{chars}"
            shown = result.composition
        else:
            document = f"{document}{result.commit}"
            composition = result.composition
    text = document if key_presses else f"{document}{composition}"
    return text
