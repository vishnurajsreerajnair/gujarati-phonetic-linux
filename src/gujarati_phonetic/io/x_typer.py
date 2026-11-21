"""Type text into the focused X window with simulated key presses (XTest).

Each character goes on a spare key code, one that no key of the keyboard uses,
mapped to the character's key symbol; the application reads it as a normal key
press. The engine recognises these key codes when they come back through IBus.

An application reads a key press with its own copy of the key map, updated
some time after the X server tells it of a change. A key code mapped to a new
character is therefore pressed only when the application has read every earlier
press (they all came back through IBus), and a moment after the change.

Keys without a character (Return, Tab, the arrows) go on their own key code,
as applications recognise them by the key code; they are pressed again in
their turn, after the characters still waiting.
"""

from __future__ import annotations

import time

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
        self.free: list[int] = []
        # The key code of each key symbol, the least recently used first.
        self.keycodes: dict[int, int] = {}
        # The keys to press, in order: (key symbol, key code), key code 0 for
        # a character on a spare key code.
        self.waiting: list[tuple[int, int]] = []
        # Key codes of the keyboard pressed again, not come back yet.
        self.replayed: list[int] = []
        # Presses sent that did not come back through IBus yet, and the time
        # of the last one.
        self.unread = 0
        self.last_press = 0.0

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
                    backspace, *self.free = spare
                    self.keycodes[XK.XK_BackSpace] = backspace
                else:
                    display.close()
                    self.failed = True
        return self.display is not None

    def owns(self, keycode: int) -> bool:
        """Tell whether a key press comes from this typer.

        Args:
            keycode: The X key code of the key press.

        Returns:
            Whether the key code is a spare one or a key pressed again.
        """
        return keycode in self.spare or keycode in self.replayed

    def type_text(self, backspaces: int, text: str) -> None:
        """Queue Backspace presses, then the characters of a text.

        send() presses them.

        Args:
            backspaces: The number of Backspace presses.
            text: The characters to type.
        """
        for _ in range(backspaces):
            self.waiting.append((XK.XK_BackSpace, 0))
        for char in text:
            self.waiting.append((keysym_for(char), 0))

    def type_key(self, keysym: int, keycode: int, char: str) -> None:
        """Queue a key the application would get, after the waiting keys.

        Args:
            keysym: The key symbol.
            keycode: The X key code of the key.
            char: The character the key types, "" if none; control characters
                (Return, Tab) count as none.
        """
        if char.isprintable() and char:
            # The character itself: the same with or without Shift held.
            self.waiting.append((keysym_for(char), 0))
        else:
            self.waiting.append((keysym, keycode))

    def busy(self) -> bool:
        """Tell whether keys wait, or presses were not read yet (up to 0.5 s).

        A key that goes straight to the application then would arrive before
        them; it must be queued with type_key().

        Returns:
            Whether the application has not got every key yet.
        """
        behind = self.unread > 0 and time.monotonic() - self.last_press < 0.5
        return bool(self.waiting) or behind

    def read(self, keycode: int) -> None:
        """Count a press of this typer that came back through IBus.

        Args:
            keycode: The X key code of the press.
        """
        self.unread = max(self.unread - 1, 0)
        if keycode in self.replayed:
            self.replayed.remove(keycode)

    def send(self) -> int | None:
        """Press the waiting keys that can go now, in the focused window.

        A key code that needs a new character waits until the application has
        read the earlier presses, at most 0.5 s, then gets the character; its
        press goes 80 ms later (30 ms lost characters in ONLYOFFICE).

        Returns:
            The milliseconds to wait before calling again, or None if no key
            waits.

        Raises:
            ConnectionError: If the display is not open, is gone, or refuses a
                request.
        """
        if self.display is None:
            raise ConnectionError(f"X display {self.display_name} is not open")
        delay = None
        try:
            while self.waiting and delay is None:
                keysym, own_keycode = self.waiting[0]
                if own_keycode:
                    keycode = own_keycode
                    current = keysym
                else:
                    keycode = self._keycode(keysym)
                    # Checked at every press: ChromeOS resets the key map when
                    # the keyboard layout changes.
                    mapping = self.display.get_keyboard_mapping(keycode, 1)
                    current = mapping[0][0]
                behind = time.monotonic() - self.last_press < 0.5
                if current == keysym:
                    if own_keycode:
                        self.replayed.append(keycode)
                    xtest.fake_input(self.display, X.KeyPress, keycode)
                    xtest.fake_input(self.display, X.KeyRelease, keycode)
                    self.waiting.pop(0)
                    self.unread += 1
                    self.last_press = time.monotonic()
                elif self.unread and behind:
                    # The application has not read the earlier presses.
                    delay = 20
                else:
                    self._map(self.display, keycode, keysym)
                    self.unread = 0
                    delay = 80
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
        return delay

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

    def _keycode(self, keysym: int) -> int:
        """Return the spare key code of a key symbol, taking one if needed.

        Args:
            keysym: The key symbol.

        Returns:
            The key code.
        """
        keycode = self.keycodes.pop(keysym, None)
        if keycode is None:
            if self.free:
                keycode = self.free.pop()
            else:
                # Reuse the key code of the least recently typed character; it
                # gets the new one when the application has read its presses.
                oldest = next(key for key in self.keycodes if key != XK.XK_BackSpace)
                keycode = self.keycodes.pop(oldest)
        self.keycodes[keysym] = keycode
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
