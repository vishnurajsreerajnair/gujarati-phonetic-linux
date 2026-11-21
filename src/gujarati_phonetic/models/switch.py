"""The language the keyboard types: one for every application, as on ChromeOS."""

from __future__ import annotations


class LanguageSwitch:
    """Gujarati or English, shared by every input context of the keyboard."""

    def __init__(self) -> None:
        self.gujarati = True

    def flip(self) -> bool:
        """Switch to the other language.

        Returns:
            Whether Gujarati is now on.
        """
        self.gujarati = not self.gujarati
        return self.gujarati
