"""The parsed layout: Google's ParsedLayout (parsedlayout.js) in Python."""

from __future__ import annotations

import re
from dataclasses import dataclass

from gujarati_phonetic.core.regex import expand_js_replacement, prefixalize_regex
from gujarati_phonetic.schema.layout import LayoutInput

# Marks where the last transform ended in the history text (\u001d in the
# rules), so that a rule can look behind it.
SEPARATOR = "\x1d"
# Modifier states whose key tables are reached from a physical keyboard. The
# AltGr tables ("c", "sc") are only used by ChromeOS's on-screen keyboard.
TYPING_STATES = ("", "s", "l", "sl")


@dataclass(frozen=True)
class Edit:
    """A change to the text before the cursor.

    Attributes:
        back: Number of characters to delete before the cursor.
        chars: Characters to insert after the deletion.
    """

    back: int
    chars: str


@dataclass(frozen=True)
class _Rule:
    """One transform rule, compiled.

    Attributes:
        regex: The rule anchored at the end of the text.
        replacement: The JavaScript replacement string.
    """

    regex: re.Pattern[str]
    replacement: str


class ParsedLayout:
    """A rule-based layout ready for typing.

    Args:
        layout: The layout definition.

    Raises:
        ValueError: If a key table uses the {{...}} multi-character form in a
            typing state, which this port does not read.
        re.error: If a rule is not a valid regular expression.
    """

    def __init__(self, layout: LayoutInput) -> None:
        self.layout_id = layout.layout_id
        self.title = layout.title
        # The characters a US keyboard sends that the layout accepts.
        tables = [layout.mappings[state][""] for state in TYPING_STATES]
        if any("{{" in table for table in tables):
            raise ValueError(f"{layout.layout_id}: {{{{...}}}} keys are not supported")
        self.typeable = frozenset("".join(tables))
        # The rules: one long alternation to find the rule that matches, and
        # each rule by the number of its group in the alternation.
        rules: dict[int, _Rule] = {}
        alone = []
        partial = []
        group = 1
        for pattern, replacement in layout.transforms:
            rules[group] = _Rule(re.compile(f"{pattern}$"), replacement)
            alone.append(f"({pattern}$)")
            partial.append(f"^({prefixalize_regex(pattern)})")
            group += re.compile(pattern).groups + 1
        self._rules = rules
        self._longest = re.compile("|".join(alone))
        self._prefix = re.compile("|".join(partial))
        self._prefix_reversed = re.compile("|".join(reversed(partial)))
        self._ambiguous = re.compile(f"^({layout.history_prune_regex})$")

    def predict_transform(self, text: str) -> int:
        """Find where a later key could still transform the text.

        Port of ParsedLayout.predictTransform.

        Args:
            text: The history text, with the separator.

        Returns:
            The position from which the text may still change, -1 if none.
        """
        position = -1
        start = 0
        while position < 0 and start < len(text):
            tail = text[start:]
            forward = self._prefix.search(tail)
            if forward and forward.group(0):
                count = len(forward.groups()) + 1
                matched = next((j for j in range(1, count) if forward.group(j)), count)
                backward = self._prefix_reversed.search(tail)
                if backward and backward.group(0):
                    reversed_index = next(
                        (j for j in range(1, count) if backward.group(j)), count
                    )
                    # The tail is a prefix when different rules match each
                    # way, or when the same rule does not match it whole.
                    whole = re.search(
                        f"{self._rules[matched].regex.pattern}\x01", f"{tail}\x01"
                    )
                    if matched != count - reversed_index or not whole:
                        position = start
            start += 1
        return position

    def transform(self, previous: str, transat: int, chars: str) -> Edit | None:
        """Apply the rules to the history text plus the typed characters.

        Port of ParsedLayout.transform.

        Args:
            previous: The history text.
            transat: Where the last transform ended in it, -1 if none.
            chars: The typed characters.

        Returns:
            The edit relative to the history text, None if no rule matches.
        """
        if transat > 0:
            text = f"{previous[:transat]}{SEPARATOR}{previous[transat:]}{chars}"
        else:
            text = f"{previous}{chars}"
        edit = None
        found = self._longest.search(text)
        if found:
            count = len(found.groups()) + 1
            group = next((i for i in range(1, count) if found.group(i)), count)
            rule = self._rules[group]
            match = rule.regex.search(text)
            if match:
                # The separator is not in the visible text.
                removed = text[match.start() :]
                separators = 1 if SEPARATOR in removed else 0
                back = len(removed) - separators - len(chars)
                replaced = rule.regex.sub(
                    lambda m: expand_js_replacement(m, rule.replacement), text, count=1
                )
                inserted = replaced[match.start() :].replace(SEPARATOR, "", 1)
                edit = Edit(back, inserted)
        return edit

    def is_ambiguous(self, chars: str) -> bool:
        """Tell whether typed characters may still change meaning.

        Port of ParsedLayout.isAmbiChars.

        Args:
            chars: The typed characters.

        Returns:
            Whether they match the layout's history prune pattern.
        """
        return bool(self._ambiguous.search(chars))
