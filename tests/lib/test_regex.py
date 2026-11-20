"""JavaScript regular expression behaviour reproduced in Python."""

from __future__ import annotations

import re

import pytest

from gujarati_phonetic.core.regex import expand_js_replacement, prefixalize_regex


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("abc", "(?:a|$)(?:b|$)(?:c|$)"),
        ("\\.n", "(?:\\.|$)(?:n|$)"),
        ("([ક-હ])a", "((?:[ક-હ]|$))(?:a|$)"),
        ("x?", "(?:x|$)?"),
        ("\\[a\\]", "(?:\\[|$)(?:a|$)(?:\\]|$)"),
    ],
)
def test_prefixalize(pattern: str, expected: str) -> None:
    """Each piece also matches the end, as prefixalizeRegexString_ does."""
    assert prefixalize_regex(pattern) == expected


@pytest.mark.parametrize("text", ["", "a", "ab", "abc"])
def test_prefixalized_matches_prefixes(text: str) -> None:
    """The rewritten pattern matches every prefix of a match."""
    assert re.fullmatch(prefixalize_regex("abc"), text)


def test_expand_js_replacement() -> None:
    """$1 is the group; a group that did not take part gives ""."""
    match = re.search("(k)(x)?a", "ka")
    assert match is not None
    assert expand_js_replacement(match, "$1-$2-$1") == "k--k"
