"""Type text into the focused X window with simulated key presses (XTest).

Each character goes on a spare key code, one that no key of the keyboard uses,
mapped to the character's key symbol; the application reads it as a normal key
press. The engine recognises these key codes when they come back through IBus.
"""

from __future__ import annotations

from Xlib import XK, X, error
from Xlib.display import Display
from Xlib.ext import xtest

from gujarati_phonetic.core.screen import keysym_for


class XTyper:
    """Simulated key presses on one X display, opened on first use.

    Args:
        display_name: The X display, for example ":0".
    """

    def __init__(self, display_name: str) -> None:
        self.display_name = display_name
        self.display: Display | None = None
        self.failed = False
        # Key symbols per key code in the display's key map.
        self.width = 0
        # Spare key codes: one for Backspace, the others for the characters.
        self.spare: frozenset[int] = frozenset()
        self.backspace = 0
        self.free: list[int] = []
        # The key code of each character, the least recently used first.
        self.keycodes: dict[str, int] = {}

    def ready(self) -> bool:
        """Open the display on the first call, and tell whether it can type.

        A display that fails to open is not tried again.

        Returns:
            Whether the display is open, with XTest and spare key codes.
        """
        if self.display is None and not self.failed:
            try:
                display = Display(self.display_name)
                first = display.display.info.min_keycode
                last = display.display.info.max_keycode
                mapping = display.get_keyboard_mapping(first, last - first + 1)
                has_xtest = display.has_extension("XTEST")
            except (error.DisplayError, error.ConnectionClosedError, error.XError):
                self.failed = True
            else:
                # Key code 8 is the reserved key (evdev 0), that X servers may
                # ignore.
                spare = []
                for index, syms in enumerate(mapping):
                    keycode = first + index
                    if not any(syms) and keycode >= 9:
                        spare.append(keycode)
                if has_xtest and len(spare) >= 2:
                    self.display = display
                    self.width = len(mapping[0])
                    self.spare = frozenset(spare)
                    self.backspace, *self.free = spare
                else:
                    display.close()
                    self.failed = True
        return self.display is not None

    def owns(self, keycode: int) -> bool:
        """Tell whether a key press comes from this typer.

        Args:
            keycode: The X key code of the key press.

        Returns:
            Whether the key code is one of the spare key codes.
        """
        return keycode in self.spare

    def type_text(self, backspaces: int, text: str) -> None:
        """Press Backspace, then type text, in the focused window.

        Args:
            backspaces: The number of Backspace presses.
            text: The characters to type.

        Raises:
            ConnectionError: If the display is not open, is gone, or refuses a
                request.
        """
        if self.display is None:
            raise ConnectionError(f"X display {self.display_name} is not open")
        try:
            for _ in range(backspaces):
                self._press(self.display, self.backspace, XK.XK_BackSpace)
            for char in text:
                keycode = self._keycode(char)
                keysym = keysym_for(char)
                self._press(self.display, keycode, keysym)
            self.display.sync()
            # Drop the events X sends back (MappingNotify), never read.
            for _ in range(self.display.pending_events()):
                self.display.next_event()
        except (error.ConnectionClosedError, error.XError) as failure:
            # Not tried again: the clients get IBus text instead.
            self.display = None
            self.failed = True
            raise ConnectionError(
                f"X display {self.display_name} stopped the key presses"
            ) from failure

    def close(self) -> None:
        """Unmap the spare key codes and close the display, if open.

        Raises:
            ConnectionError: If the display is gone.
        """
        if self.display is not None:
            try:
                for keycode in self.spare:
                    self._map(self.display, keycode, X.NoSymbol)
                self.display.close()
            except (error.ConnectionClosedError, error.XError) as failure:
                raise ConnectionError(
                    f"X display {self.display_name} is gone"
                ) from failure
            self.display = None

    def _keycode(self, char: str) -> int:
        """Return the spare key code of a character, taking one if needed.

        Args:
            char: One character.

        Returns:
            The key code.
        """
        keycode = self.keycodes.pop(char, None)
        if keycode is None:
            if self.free:
                keycode = self.free.pop()
            else:
                # Reuse the key code of the least recently typed character. Its
                # earlier presses are read before the new mapping arrives.
                oldest = next(iter(self.keycodes))
                keycode = self.keycodes.pop(oldest)
        self.keycodes[char] = keycode
        return keycode

    def _map(self, display: Display, keycode: int, keysym: int) -> None:
        """Give a key code one key symbol, at every shift level.

        Args:
            display: The open display.
            keycode: The key code.
            keysym: The key symbol.
        """
        keysyms = [(keysym,) * self.width]
        display.change_keyboard_mapping(keycode, keysyms)
        display.sync()

    def _press(self, display: Display, keycode: int, keysym: int) -> None:
        """Press and release a spare key code, mapped to a key symbol.

        The mapping is checked at every press: ChromeOS resets the key map
        when the keyboard layout changes.

        Args:
            display: The open display.
            keycode: The key code.
            keysym: The key symbol it must type.
        """
        mapping = display.get_keyboard_mapping(keycode, 1)
        current = mapping[0][0]
        if current != keysym:
            self._map(display, keycode, keysym)
        xtest.fake_input(display, X.KeyPress, keycode)
        xtest.fake_input(display, X.KeyRelease, keycode)
