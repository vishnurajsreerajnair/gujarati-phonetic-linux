"""Regular expression helpers that reproduce the JavaScript behaviour of Google's
keyboard engine (parsedlayout.js)."""

from __future__ import annotations

import re

# Pieces of a pattern, as prefixalizeRegexString_ splits it: an escape, a
# bracket class, a {...} quantifier or one plain character.
_PATTERN_PIECE = re.compile(r"\\.|\[[^\[\]]*\]|\{.*\}|[^\|\\\(\)\[\]\{\}\*\+\?]")
_JS_GROUP_REFERENCE = re.compile(r"\$(\d)")


def prefixalize_regex(pattern: str) -> str:
    """Rewrite a pattern so that it also matches every prefix of its matches.

    Port of ParsedLayout.prefixalizeRegexString_: each piece p becomes
    (?:p|$), so "abc" matches "a", "ab" and "abc".

    Args:
        pattern: The rule's regular expression.

    Returns:
        The prefix-matching regular expression.
    """
    # Hide escaped brackets so that the bracket classes stay whole.
    hidden = re.sub(
        r"\\.",
        lambda m: {"\\[": "\x01", "\\]": "\x02"}.get(m.group(0), m.group(0)),
        pattern,
    )
    # Let each piece also match the end of the text.
    prefixed = _PATTERN_PIECE.sub(
        lambda m: m.group(0) if m.group(0).startswith("{") else f"(?:{m.group(0)}|$)",
        hidden,
    )
    return prefixed.replace("\x01", "\\[").replace("\x02", "\\]")


def expand_js_replacement(match: re.Match[str], replacement: str) -> str:
    """Expand a JavaScript replacement string ($1 to $9) for a match.

    Args:
        match: The match of the rule.
        replacement: The rule's replacement, with $n group references.

    Returns:
        The replacement text; a group that did not take part gives "", as in
        JavaScript.
    """
    return _JS_GROUP_REFERENCE.sub(
        lambda m: match.group(int(m.group(1))) or "", replacement
    )
