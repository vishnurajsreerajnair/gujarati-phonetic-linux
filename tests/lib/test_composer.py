"""Readable examples of the keyboard, as a user types."""

from __future__ import annotations

import pytest

from gujarati_phonetic.models.composer import BACKSPACE, Composer
from gujarati_phonetic.models.parsed_layout import ParsedLayout


def type_text(layout: ParsedLayout, keys: str) -> str:
    """Type keys and return the text that ends up in the document.

    Args:
        layout: The parsed layout.
        keys: The keys typed.

    Returns:
        Everything committed, with the keys the application typed itself, then
        the composition committed by a reset.
    """
    composer = Composer(layout)
    text = ""
    for key in keys:
        result = composer.type_key(key)
        # A key the keyboard does not use is typed by the application.
        text = f"{text}{result.commit}" if result.handled else f"{text}{key}"
    return f"{text}{composer.reset()}"


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        ("kem Cho", "કેમ છો"),
        ("namaste", "નમસ્તે"),
        ("gujarAtI", "ગુજરાતી"),
        ("gujaraatii", "ગુજરાતી"),
        ("bhAShA", "ભાષા"),
        ("dhanyavAd", "ધન્યવાદ"),
        ("kShamA", "ક્ષમા"),
        ("j~nAna", "જ્ઞાન"),
        ("vidyArthI", "વિદ્યાર્થી"),
        ("taiyAr", "તૈયાર"),
        ("auShadh", "ઔષધ"),
        ("OM", "ૐ"),
        ("sha.nkar", "શંકર"),
        ("ka", "ક"),
        ("kaa", "કા"),
        ("kk", "ક્ક"),
        ("satya", "સત્ય"),
        ("nyAy", "ન્યાય"),
        ("kY", "ક્ય઼"),
        ("kem Cho, majAmAM?", "કેમ છો, મજામાં?"),
    ],
)
def test_words(layout: ParsedLayout, keys: str, expected: str) -> None:
    """Common words come out as written Gujarati."""
    assert type_text(layout, keys) == expected


def test_space_commits_the_word(layout: ParsedLayout) -> None:
    """The word stays composed until Space commits it with the space."""
    composer = Composer(layout)
    for key in "kem":
        composer.type_key(key)
    result = composer.type_key(" ")
    assert (result.handled, result.commit, result.composition) == (True, "કેમ ", "")


def test_backspace_edits_the_composition(layout: ParsedLayout) -> None:
    """Backspace removes the last letter of the word being typed."""
    composer = Composer(layout)
    for key in "kem":
        composer.type_key(key)
    result = composer.type_key(BACKSPACE)
    assert (result.handled, result.composition) == (True, "કે")


def test_space_and_backspace_pass_when_nothing_is_composed(
    layout: ParsedLayout,
) -> None:
    """With no word in progress the application gets Space and Backspace."""
    composer = Composer(layout)
    assert not composer.type_key(" ").handled
    assert not composer.type_key(BACKSPACE).handled


def test_other_keys_pass(layout: ParsedLayout) -> None:
    """Keys that are not on a US keyboard's typing area go to the application."""
    composer = Composer(layout)
    assert not composer.type_key("\n").handled
    assert not composer.type_key("é").handled


def test_reset_commits_and_forgets(layout: ParsedLayout) -> None:
    """A reset commits the word and the next key starts a new word."""
    composer = Composer(layout)
    composer.type_key("k")
    assert composer.reset() == "ક"
    result = composer.type_key("h")
    assert result.composition == "હ"
