"""The typing history: Google's Model (model.js) in Python."""

from __future__ import annotations

from dataclasses import dataclass, replace

from gujarati_phonetic.models.parsed_layout import SEPARATOR, Edit, ParsedLayout


@dataclass(frozen=True)
class History:
    """A history text and where its last transform ended.

    Attributes:
        text: The text of the current word, as shown.
        transat: Position where the last transform ended, -1 if none.
    """

    text: str = ""
    transat: int = -1


class Model:
    """The history state that lets later keys change earlier letters.

    Args:
        layout: The parsed layout.
    """

    def __init__(self, layout: ParsedLayout) -> None:
        self.layout = layout
        # The history before the ambiguous keys, the ambiguous keys typed
        # since ("a" then "a" may become "aa"), and the current history.
        self.previous = History()
        self.ambiguous = ""
        self.current = History()

    def predict_history(self) -> int:
        """Find where later keys could still change the current text.

        Port of Model.predictHistory.

        Returns:
            The position from which the text may still change, -1 if none.
        """
        layout = self.layout
        position = -1
        # A pending ambiguous key keeps the whole text open.
        if self.ambiguous:
            text, transat = self.previous.text, self.previous.transat
            if transat > 0:
                text = f"{text[:transat]}{SEPARATOR}{text[transat:]}{self.ambiguous}"
            else:
                text = f"{text}{self.ambiguous}"
            if layout.predict_transform(text) >= 0:
                position = 0
        if position < 0:
            text, transat = self.current.text, self.current.transat
            if transat >= 0:
                text = f"{text[:transat]}{SEPARATOR}{text[transat:]}"
            position = layout.predict_transform(text)
            # The separator is not in the visible text.
            if transat >= 0 and position > transat:
                position -= 1
        return position

    def translate(self, chars: str, chars_before_caret: str) -> Edit:
        """Apply a typed key to the history.

        Port of Model.translate.

        Args:
            chars: The characters of the key.
            chars_before_caret: The composition text before the caret.

        Returns:
            The edit to the composition text.
        """
        layout = self.layout
        self._match_history(chars_before_caret)
        # With ambiguous keys pending, transform from the history before them:
        # "k" "a" then "a" is "k" + "aa".
        result = None
        if self.ambiguous:
            result = layout.transform(
                self.previous.text,
                self.previous.transat,
                f"{self.ambiguous}{chars}",
            )
            if result and result.back < 0:
                result = None
        if result:
            # Make the edit relative to the current history.
            previous = self.previous.text
            text = f"{previous[: len(previous) - result.back]}{result.chars}"
            result = Edit(len(self.current.text), text)
        else:
            result = layout.transform(self.current.text, self.current.transat, chars)
        # Keep the ambiguous keys for the next key.
        if layout.is_ambiguous(f"{self.ambiguous}{chars}"):
            if not self.ambiguous:
                self.previous = self.current
            self.ambiguous = f"{self.ambiguous}{chars}"
        elif layout.is_ambiguous(chars):
            self.previous = self.current
            self.ambiguous = chars
        else:
            self.previous = History()
            self.ambiguous = ""
        # Apply the edit to the current history.
        text, transat = self.current.text, self.current.transat
        if result:
            text = f"{text[: len(text) - result.back]}{result.chars}"
            transat = len(text)
        else:
            text = f"{text}{chars}"
            result = Edit(0, chars)
        # The history holds only the current word.
        space = text.rfind(" ")
        if space >= 0:
            text = text[space + 1 :]
            transat = transat - (space + 1) if transat > space else -1
        self.current = History(text, transat)
        return result

    def process_backspace(self, chars_before_caret: str) -> None:
        """Remove the last character from the history.

        Port of Model.processBackspace.

        Args:
            chars_before_caret: The composition text before the caret.
        """
        self._match_history(chars_before_caret)
        text = self.current.text
        if text:
            text = text[:-1]
            transat = min(self.current.transat, len(text))
            self.current = History(text, transat)
            if self.ambiguous:
                self.ambiguous = self.ambiguous[:-1]
            if not self.ambiguous:
                self.previous = History()
        else:
            self.clear_history()

    def clear_history(self) -> None:
        """Forget the history."""
        self.ambiguous = ""
        self.previous = History()
        self.current = History()

    def prune_history(self, count: int) -> None:
        """Drop the first characters of the history, once they are committed.

        Port of Model.pruneHistory.

        Args:
            count: Number of characters committed.
        """
        self.previous = _prune(self.previous, count)
        self.current = _prune(self.current, count)

    def _match_history(self, text: str) -> None:
        """Forget the history if it no longer matches the text before the caret.

        Args:
            text: The composition text before the caret.
        """
        history = self.current.text
        matches = text.endswith(history) or history.endswith(text)
        if not (history and text and matches):
            self.clear_history()


def _prune(history: History, count: int) -> History:
    """Drop the first characters of a history.

    Args:
        history: The history.
        count: Number of characters to drop.

    Returns:
        The shorter history.
    """
    transat = history.transat
    if transat > 0:
        transat -= count
        if transat <= 0:
            transat = -1
    return replace(history, text=history.text[count:], transat=transat)
