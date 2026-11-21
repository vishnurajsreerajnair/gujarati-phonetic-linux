"""Tests of the X key presses, on a fake X display."""

from __future__ import annotations

import time

import pytest
from Xlib import XK, X, error
from Xlib.ext import xtest

from gujarati_phonetic.core.screen import screen_edit
from gujarati_phonetic.io import x_typer
from gujarati_phonetic.io.x_typer import XTyper
from gujarati_phonetic.models.composer import Composer
from gujarati_phonetic.models.parsed_layout import ParsedLayout


class FakeInfo:
    """The connection info of the fake display."""

    min_keycode = 8
    max_keycode = 20


class FakeConnection:
    """The low-level connection of the fake display."""

    info = FakeInfo()


class FakeDisplay:
    """An X display with a key map, that decodes key presses into text.

    Key codes 8, 13, 14 and 15 are spare (no key symbol); the others are keys.
    Each key press is read with the key map of the moment, as an X application
    does.

    Args:
        name: The display name.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.display = FakeConnection()
        self.width = 3
        self.keymap: dict[int, int] = {}
        for keycode in range(8, 21):
            spare = keycode in (8, 13, 14, 15)
            keysym = X.NoSymbol if spare else XK.XK_a + keycode
            self.keymap[keycode] = keysym
        self.text = ""
        # Key codes of the presses the application has not read yet (see
        # send_all).
        self.unread: list[int] = []
        self.mapping_changes = 0
        self.closed = False
        self.xtest = True

    def get_keyboard_mapping(self, first: int, count: int) -> list[list[int]]:
        """Return the key symbols of key codes."""
        rows = []
        for keycode in range(first, first + count):
            rows.append([self.keymap[keycode]] * self.width)
        return rows

    def change_keyboard_mapping(
        self,
        first: int,
        keysyms: list[tuple[int, ...]],
    ) -> None:
        """Map key codes to key symbols."""
        for offset, row in enumerate(keysyms):
            self.keymap[first + offset] = row[0]
        self.mapping_changes += 1

    def has_extension(self, name: str) -> bool:
        """Tell whether the display has XTEST."""
        return name == "XTEST" and self.xtest

    def press(self, keycode: int) -> None:
        """Read a key press into the text, with the current key map."""
        self.unread.append(keycode)
        keysym = self.keymap[keycode]
        if keysym == XK.XK_BackSpace:
            self.text = self.text[:-1]
        elif keysym >= 0x01000000:
            self.text = f"{self.text}{chr(keysym - 0x01000000)}"
        else:
            self.text = f"{self.text}{chr(keysym)}"

    def sync(self) -> None:
        """Nothing to wait for."""

    def pending_events(self) -> int:
        """No events."""
        return 0

    def next_event(self) -> None:
        """No events."""

    def close(self) -> None:
        """Close the display."""
        self.closed = True


def send_all(typer: XTyper, display: FakeDisplay) -> int:
    """Send the waiting keys as the engine does, the application reading each.

    Args:
        typer: The typer, with keys waiting.
        display: Its fake display.

    Returns:
        The number of calls of send().
    """
    calls = 0
    delay: int | None = 0
    while delay is not None:
        delay = typer.send()
        calls += 1
        # The presses come back through IBus.
        for keycode in display.unread:
            typer.read(keycode)
        display.unread.clear()
    return calls


@pytest.fixture
def fake_display(monkeypatch: pytest.MonkeyPatch) -> list[FakeDisplay]:
    """Replace the X display and XTest with fakes; collect the displays opened."""
    opened: list[FakeDisplay] = []

    def open_display(name: str) -> FakeDisplay:
        display = FakeDisplay(name)
        opened.append(display)
        return display

    def fake_input(display: FakeDisplay, event_type: int, keycode: int) -> None:
        if event_type == X.KeyPress:
            display.press(keycode)

    monkeypatch.setattr(x_typer, "Display", open_display)
    monkeypatch.setattr(xtest, "fake_input", fake_input)
    return opened


def test_ready_takes_the_spare_key_codes(fake_display: list[FakeDisplay]) -> None:
    """The typer opens the display once and uses only spare key codes from 9."""
    typer = XTyper(":0")
    assert typer.ready()
    assert typer.ready()
    assert len(fake_display) == 1
    assert fake_display[0].name == ":0"
    assert typer.spare == frozenset({13, 14, 15})
    assert typer.keycodes == {XK.XK_BackSpace: 13}
    assert typer.owns(13)
    assert not typer.owns(8)
    assert not typer.owns(9)


def test_types_text_and_backspace(fake_display: list[FakeDisplay]) -> None:
    """Characters and Backspace reach the window as typed."""
    typer = XTyper(":0")
    assert typer.ready()
    typer.type_text(0, "કેમ")
    typer.type_text(1, "મ્")
    send_all(typer, fake_display[0])
    assert fake_display[0].text == "કેમ્"


def test_reuses_key_codes_for_many_characters(
    fake_display: list[FakeDisplay],
) -> None:
    """With two spare key codes for characters, every character still arrives."""
    typer = XTyper(":0")
    assert typer.ready()
    text = "ગુજરાતી નમસ્તે"
    typer.type_text(0, text)
    send_all(typer, fake_display[0])
    assert fake_display[0].text == text


def test_remaps_when_the_key_map_was_reset(fake_display: list[FakeDisplay]) -> None:
    """A key map reset by the system is fixed before the next press."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    typer.type_text(0, "ક")
    send_all(typer, display)
    for keycode in typer.spare:
        display.keymap[keycode] = X.NoSymbol
    typer.type_text(0, "ક")
    send_all(typer, display)
    assert display.text == "કક"


def test_no_xtest_is_not_ready(
    fake_display: list[FakeDisplay],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without XTest the typer is not ready, closes the display, never retries."""

    def open_without_xtest(name: str) -> FakeDisplay:
        display = FakeDisplay(name)
        display.xtest = False
        fake_display.append(display)
        return display

    monkeypatch.setattr(x_typer, "Display", open_without_xtest)
    typer = XTyper(":0")
    assert not typer.ready()
    assert not typer.ready()
    assert len(fake_display) == 1
    assert fake_display[0].closed


def test_display_that_cannot_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """A display that cannot be opened makes the typer not ready."""

    def refuse(name: str) -> FakeDisplay:
        raise error.DisplayConnectionError(name, "refused")

    monkeypatch.setattr(x_typer, "Display", refuse)
    typer = XTyper(":9")
    assert not typer.ready()
    typer.type_text(0, "ક")
    with pytest.raises(ConnectionError):
        typer.send()


def test_close_unmaps_the_spare_key_codes(fake_display: list[FakeDisplay]) -> None:
    """Closing gives the spare key codes back and closes the display."""
    typer = XTyper(":0")
    assert typer.ready()
    typer.type_text(0, "કા")
    send_all(typer, fake_display[0])
    typer.close()
    display = fake_display[0]
    assert display.closed
    for keycode in (13, 14, 15):
        assert display.keymap[keycode] == X.NoSymbol


@pytest.mark.parametrize(
    "keys",
    [
        "kem Cho ",
        "gujaraatii ",
        "vidyArthI ",
        "sa\b\bshA ",
        "kemm\b ",
        "namaste duniyA ",
    ],
)
def test_engine_key_presses_on_the_display(
    fake_display: list[FakeDisplay],
    layout: ParsedLayout,
    keys: str,
) -> None:
    """The engine's key presses mode leaves the same text as IBus text."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    composer = Composer(layout)
    shown = ""
    by_text = ""
    composition = ""
    for key in keys:
        result = composer.type_key(key)
        if not result.handled:
            # The application gets the real key.
            if key == "\b":
                display.text = display.text[:-1]
                by_text = by_text[:-1]
            else:
                display.text = f"{display.text}{key}"
                by_text = f"{by_text}{key}"
            continue
        text = f"{result.commit}{result.composition}"
        backspaces, chars = screen_edit(shown, text)
        typer.type_text(backspaces, chars)
        send_all(typer, display)
        shown = result.composition
        by_text = f"{by_text}{result.commit}"
        composition = result.composition
    assert display.text == f"{by_text}{composition}"


def test_new_character_waits_for_the_earlier_presses(
    fake_display: list[FakeDisplay],
) -> None:
    """A key code gets a new character only when the earlier presses are read."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    typer.type_text(0, "કે")
    # ક needs a key code: mapped, pressed 80 ms later.
    assert typer.send() == 80
    assert display.text == ""
    # ક goes; ે waits for the application to read it.
    assert typer.send() == 20
    assert display.text == "ક"
    changes = display.mapping_changes
    assert typer.send() == 20
    assert display.mapping_changes == changes
    typer.read(display.unread[0])
    assert typer.send() == 80
    assert typer.send() is None
    assert display.text == "કે"


def test_mapped_characters_go_at_once(fake_display: list[FakeDisplay]) -> None:
    """Characters already on a key code go without waiting."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    typer.type_text(0, "કે")
    send_all(typer, display)
    typer.type_text(0, "કેકે")
    assert typer.send() is None
    assert display.text == "કેકેકે"


def test_unread_presses_stop_waiting_after_half_a_second(
    fake_display: list[FakeDisplay],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the presses never come back, the next character goes after 0.5 s."""

    def start() -> float:
        return 100.0

    def later() -> float:
        return 100.6

    monkeypatch.setattr(time, "monotonic", start)
    typer = XTyper(":0")
    assert typer.ready()
    typer.type_text(0, "કે")
    assert typer.send() == 80
    assert typer.send() == 20
    monkeypatch.setattr(time, "monotonic", later)
    assert typer.send() == 80
    assert typer.send() is None
    assert fake_display[0].text == "કે"


def test_keys_go_after_the_waiting_text(fake_display: list[FakeDisplay]) -> None:
    """A key for the application is pressed after the characters before it."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    typer.type_text(0, "ક")
    # A printable key goes as its character, on a spare key code.
    typer.type_key(XK.XK_question, 61, "?")
    # A key without a character goes on its own key code (here key code 9).
    typer.type_key(XK.XK_a + 9, 9, "\r")
    send_all(typer, display)
    assert display.text == f"ક?{chr(XK.XK_a + 9)}"
    assert 61 not in display.unread


def test_replayed_key_is_owned_until_read(fake_display: list[FakeDisplay]) -> None:
    """A key pressed again is recognised once when it comes back."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    typer.type_key(XK.XK_a + 9, 9, "")
    assert typer.busy()
    assert typer.send() is None
    assert typer.owns(9)
    assert display.unread == [9]
    typer.read(9)
    assert not typer.owns(9)
    assert display.text == chr(XK.XK_a + 9)


def test_busy_until_the_presses_are_read(fake_display: list[FakeDisplay]) -> None:
    """The typer is busy while keys wait or presses are not read yet."""
    typer = XTyper(":0")
    assert typer.ready()
    display = fake_display[0]
    assert not typer.busy()
    typer.type_text(0, "ક")
    assert typer.busy()
    send_all(typer, display)
    assert not typer.busy()
