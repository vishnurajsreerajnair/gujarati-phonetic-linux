"""Talk to the running keyboard through ibus-daemon, as an application would."""

from __future__ import annotations

import time

import gi

gi.require_version("IBus", "1.0")
from gi.repository import Gio, GLib, IBus


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
    # The global engine, as the start-up script sets it: setting the engine of
    # one input context does not take effect on every IBus version.
    if not bus.set_global_engine(engine_name):
        raise LookupError(f"IBus engine {engine_name} cannot be started")
    context.focus_in()
    _wait_for_signals(0.2)
    for key in keys:
        # PyGObject takes the character as a string.
        keyval = IBus.KEY_space if key == " " else IBus.unicode_to_keyval(key)
        handled = context.process_key_event(keyval, 0, 0)
        _wait_for_signals(0.2)
        if not handled:
            received.append(key)
    text = f"{''.join(received)}{composition}"
    context.destroy()
    return text


def toggle_language() -> str:
    """Switch the running keyboard between Gujarati and English.

    Returns:
        The language now on: "gujarati" or "english".

    Raises:
        ConnectionError: If ibus-daemon or the keyboard is not running.
    """
    IBus.init()
    bus = IBus.Bus()
    if not bus.is_connected():
        raise ConnectionError("cannot connect to ibus-daemon; is it running?")
    connection = bus.get_connection()
    # The Toggle method of the engine process (ibus_engine.run).
    try:
        reply = connection.call_sync(
            "org.freedesktop.IBus.GujaratiPhonetic",
            "/org/freedesktop/IBus/GujaratiPhonetic",
            "org.freedesktop.IBus.GujaratiPhonetic.Language",
            "Toggle",
            None,
            GLib.VariantType.new("(s)"),
            Gio.DBusCallFlags.NONE,
            2000,
            None,
        )
    except GLib.Error as error:
        raise ConnectionError(
            f"the Gujarati keyboard is not running: {error.message}"
        ) from error
    (language,) = reply.unpack()
    return str(language)


def _wait_for_signals(seconds: float) -> None:
    """Let the main loop deliver the signals ibus-daemon sent.

    Args:
        seconds: How long to wait; ibus-daemon delivers the text of a key in
            well under 0.2 s.
    """
    main_context = GLib.MainContext.default()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        main_context.iteration(False)
        time.sleep(0.01)
