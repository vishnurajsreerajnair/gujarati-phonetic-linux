"""The keyboard layout, as Google's ChromeOS layout files define it."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class LayoutInput:
    """A ChromeOS rule-based keyboard layout (for example gu_phone.js).

    Attributes:
        layout_id: Layout code, for example "gu_phone".
        title: Layout name shown to the user.
        mappings: Key tables by modifier state ("", "s", "l", "sl", "c",
            "sc"): each maps "" to the characters of the keys in keyboard
            order.
        transforms: The rules in file order, as (regular expression,
            replacement) pairs. The order matters: the first rule that matches
            wins.
        history_prune_regex: Regular expression of the typed text that may
            still change meaning (for example "a" before "aa").
    """

    layout_id: str
    title: str
    mappings: dict[str, dict[str, str]]
    transforms: list[tuple[str, str]]
    history_prune_regex: str
