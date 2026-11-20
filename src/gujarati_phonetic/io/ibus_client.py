"""Type through ibus-daemon as an application would, to check the installation."""

from __future__ import annotations

import time

import gi

gi.require_version("IBus", "1.0")
from gi.repository import GLib, IBus

# How long to wait for ibus-daemon to deliver the text of a key, in seconds.
SIGNAL_WAIT = 0.2


def type_through_ibus(engine_name: str, keys: str) -> str:
    """Type keys into a new input context and return the text it receives.

    Args:
        engine_name: The IBus engine to use, for example "gujarati-phonetic".
        keys: The keys to type.

    Returns:
        The text an application would contain: the committed text, the keys
        the engine let through, then the composition left at the end.

    Raises:
        ConnectionError: If ibus-daemon is not running.
        LookupError: If the engine is not installed.
    """
    IBus.init()
    bus = IBus.Bus()
    if not bus.is_connected():
        raise ConnectionError("cannot connect to ibus-daemon; is it running?")
    if not any(engine.get_name() == engine_name for engine in bus.list_engines()):
        raise LookupError(f"IBus engine {engine_name} is not installed")
    context = bus.create_input_context("gujarati-phonetic-check")
    context.set_capabilities(IBus.Capabilite.PREEDIT_TEXT | IBus.Capabilite.FOCUS)
    # Collect what the engine sends, as an application does.
    received: list[str] = []
    composition = ""

    def on_commit(_context: IBus.InputContext, text: IBus.Text) -> None:
        received.append(text.get_text())

    def on_composition(
        _context: IBus.InputContext, text: IBus.Text, _cursor: int, _visible: bool
    ) -> None:
        nonlocal composition
        composition = text.get_text()

    context.connect("commit-text", on_commit)
    context.connect("update-preedit-text", on_composition)
    context.focus_in()
    context.set_engine(engine_name)
    _wait_for_signals()
    for key in keys:
        # PyGObject takes the character as a string.
        keyval = IBus.KEY_space if key == " " else IBus.unicode_to_keyval(key)
        handled = context.process_key_event(keyval, 0, 0)
        _wait_for_signals()
        if not handled:
            received.append(key)
    text = f"{''.join(received)}{composition}"
    context.destroy()
    return text


def _wait_for_signals() -> None:
    """Let the main loop deliver the signals ibus-daemon sent."""
    main_context = GLib.MainContext.default()
    deadline = time.monotonic() + SIGNAL_WAIT
    while time.monotonic() < deadline:
        main_context.iteration(False)
        time.sleep(0.01)
