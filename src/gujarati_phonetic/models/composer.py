"""Typing with a composition line: Google's ComposeTextInput
(composetextinput.js) and the key step of its Controller (controller.js)."""

from __future__ import annotations

from dataclasses import dataclass

from gujarati_phonetic.core.marks import trailing_cluster_length
from gujarati_phonetic.models.model import Model
from gujarati_phonetic.models.parsed_layout import Edit, ParsedLayout

BACKSPACE = "\b"


@dataclass(frozen=True)
class KeyResult:
    """What one key does to the text.

    Attributes:
        handled: Whether the keyboard used the key; if not, the application
            gets it.
        commit: Text to insert for good, before the composition.
        composition: The composition text shown after the key (underlined, may
            still change).
    """

    handled: bool
    commit: str
    composition: str


class Composer:
    """The Gujarati phonetic keyboard for one input field.

    Args:
        layout: The parsed layout.
    """

    def __init__(self, layout: ParsedLayout) -> None:
        self.layout = layout
        self.model = Model(layout)
        self.composition = ""

    def type_key(self, key: str) -> KeyResult:
        """Type one key.

        Port of Controller.commitChars_ for a US keyboard.

        Args:
            key: The character the key types (" " for Space), or BACKSPACE.

        Returns:
            The text to commit and the new composition.
        """
        chars = key if key != BACKSPACE and key in self.layout.typeable else ""
        if not chars and key == " ":
            chars = " "
        if not chars and key != BACKSPACE:
            result = KeyResult(False, "", self.composition)
        elif key == BACKSPACE:
            self.model.process_backspace(self.composition)
            result = self._commit_text(Edit(1, ""))
        else:
            result = self._commit_text(self.model.translate(chars, self.composition))
        return result

    def reset(self) -> str:
        """Finish the word: commit the composition and forget the history.

        Port of ComposeTextInput.reset, plus the history reset that ChromeOS
        does when the focus or the caret moves.

        Returns:
            The text to commit, "" if none.
        """
        text = self.composition
        self.composition = ""
        self.model.clear_history()
        return text

    def _commit_text(self, edit: Edit) -> KeyResult:
        """Apply an edit to the composition and commit what can no longer change.

        Port of ComposeTextInput.commitText.

        Args:
            edit: The edit from the model.

        Returns:
            The text to commit and the new composition.
        """
        on_stage = bool(self.composition)
        commit = ""
        handled = True
        # Backspace or Space with nothing composed: the application handles it.
        is_backspace = edit.back == 1 and not edit.chars
        is_space = edit.back == 0 and edit.chars == " "
        if not on_stage and (is_backspace or is_space):
            handled = False
        # Space ends the word.
        elif on_stage and is_space:
            commit = f"{self.composition} "
            self.composition = ""
        else:
            length = len(self.composition)
            text = f"{self.composition[: length - edit.back]}{edit.chars}"
            if not text:
                self.composition = text
            else:
                # Commit the part that later keys can no longer change, without
                # splitting a letter from its signs.
                position = self.model.predict_history()
                if position > 0:
                    head = text[: position + 1]
                    cluster = trailing_cluster_length(head)
                    if cluster is not None:
                        position = len(head) - cluster
                if position < 0:
                    commit = text
                    self.composition = ""
                    self.model.clear_history()
                elif position == 0:
                    self.composition = text
                else:
                    commit = text[:position]
                    self.composition = text[position:]
                    self.model.prune_history(position)
        return KeyResult(handled, commit, self.composition)
