"""The IBus input method engine: connects the keyboard to Linux applications."""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

import gi

gi.require_version("IBus", "1.0")
from gi.repository import Gio, IBus

from gujarati_phonetic.core.keys import KeyAction, classify_key
from gujarati_phonetic.core.screen import screen_edit
from gujarati_phonetic.models.composer import BACKSPACE, Composer, KeyResult
from gujarati_phonetic.models.parsed_layout import ParsedLayout

if TYPE_CHECKING:
    from gujarati_phonetic.io.x_typer import XTyper


class GujaratiPhoneticEngine(IBus.Engine):
    """One keyboard instance, created by run() for each IBus input context.

    Args:
        engine_name: The engine name, as in the IBus component file.
        object_path: The D-Bus object path of the instance.
        connection: The connection to ibus-daemon.
        layout: The parsed layout.
        typer: The key presses for the clients that drop IBus text, shared by
            all instances; None without python3-xlib.
    """

    __gtype_name__ = "GujaratiPhoneticEngine"

    def __init__(
        self,
        engine_name: str,
        object_path: str,
        connection: Gio.DBusConnection,
        layout: ParsedLayout,
        typer: XTyper | None,
    ) -> None:
        # has_focus_id: IBus tells the client name on focus (focus-in-id).
        super().__init__(
            engine_name=engine_name,
            object_path=object_path,
            connection=connection,
            has_focus_id=True,
        )
        self.composer = Composer(layout)
        self.typer = typer
        self.gujarati = True
        # Key presses mode: the composition is typed in the document, as
        # `shown`, instead of being sent to the client.
        self.key_presses = False
        self.shown = ""

    def do_process_key_event(self, keyval: int, keycode: int, state: int) -> bool:
        """Handle a key press.

        Args:
            keyval: The X key symbol.
            keycode: The hardware key code (the X key code minus 8).
            state: The modifier mask.

        Returns:
            Whether the key was used; if not, the application gets it.
        """
        handled = False
        # The keyboard's own key presses go to the application as they are.
        own_key = (
            self.key_presses and self.typer is not None and self.typer.owns(keycode + 8)
        )
        if not own_key and not state & IBus.ModifierType.RELEASE_MASK:
            # PyGObject gives the character as a string ("" or "\x00" if none).
            code = IBus.keyval_to_unicode(keyval)
            char = "" if code == "\x00" else code
            is_space = keyval == IBus.KEY_space
            # The Search key of a Chromebook arrives as Super, Meta, Hyper or
            # Mod4.
            meta = (
                IBus.ModifierType.SUPER_MASK
                | IBus.ModifierType.META_MASK
                | IBus.ModifierType.HYPER_MASK
                | IBus.ModifierType.MOD4_MASK
            )
            action = classify_key(
                char,
                is_space,
                keyval == IBus.KEY_BackSpace,
                bool(state & IBus.ModifierType.CONTROL_MASK),
                bool(state & IBus.ModifierType.MOD1_MASK),
                bool(state & meta),
            )
            match action:
                case KeyAction.TOGGLE:
                    self._finish_word()
                    self.gujarati = not self.gujarati
                    handled = True
                case _ if not self.gujarati:
                    handled = False
                case KeyAction.TYPE:
                    key = " " if is_space else char
                    handled = self._show(self.composer.type_key(key))
                case KeyAction.BACKSPACE:
                    handled = self._show(self.composer.type_key(BACKSPACE))
                case KeyAction.PASS:
                    self._finish_word()
                    handled = False
        return handled

    def do_focus_in_id(self, object_path: str, client: str) -> None:
        """Choose how to give the text to the client that gets the focus.

        Qt 5 names its IBus client "QIBusInputContext". ONLYOFFICE bundles Qt
        5.9, which drops the text of input methods, so the keyboard types
        there with key presses.

        Args:
            object_path: The input context (unused).
            client: The client name.
        """
        self.key_presses = (
            client == "QIBusInputContext"
            and self.typer is not None
            and self.typer.ready()
        )
        self.shown = ""

    def do_focus_out_id(self, object_path: str) -> None:
        """Forget the word; its text is already in the client.

        Args:
            object_path: The input context (unused).
        """
        self.composer.reset()
        self.shown = ""

    def do_focus_out(self) -> None:
        """Forget the word.

        IBus commits the composition itself (commit mode), or its text is
        already in the client (key presses mode).
        """
        self.composer.reset()
        self.shown = ""

    def do_reset(self) -> None:
        """Forget the word.

        IBus commits the composition itself (commit mode), or its text is
        already in the client (key presses mode).
        """
        self.composer.reset()
        self.shown = ""

    def do_disable(self) -> None:
        """Finish the word when the keyboard is switched off."""
        self._finish_word()

    def _show(self, result: KeyResult) -> bool:
        """Give the client the committed text and the composition.

        As IBus text (commit and underlined composition), or as key presses for
        the clients that drop IBus text.

        Args:
            result: The result of a key.

        Returns:
            Whether the key was used.
        """
        if self.key_presses and self.typer is not None:
            text = f"{result.commit}{result.composition}"
            backspaces, chars = screen_edit(self.shown, text)
            try:
                self.typer.type_text(backspaces, chars)
            except ConnectionError:
                # The display is gone: IBus text from the next key on.
                self.key_presses = False
            self.shown = result.composition
        else:
            if result.commit:
                self.commit_text(IBus.Text.new_from_string(result.commit))
            composition = IBus.Text.new_from_string(result.composition)
            composition.append_attribute(
                IBus.AttrType.UNDERLINE,
                IBus.AttrUnderline.SINGLE,
                0,
                len(result.composition),
            )
            self.update_preedit_text_with_mode(
                composition,
                len(result.composition),
                bool(result.composition),
                IBus.PreeditFocusMode.COMMIT,
            )
        return result.handled

    def _finish_word(self) -> None:
        """Commit the composition and forget the history."""
        text = self.composer.reset()
        if self.key_presses:
            # The word is already typed in the document.
            self.shown = ""
        else:
            if text:
                self.commit_text(IBus.Text.new_from_string(text))
            empty = IBus.Text.new_from_string("")
            self.update_preedit_text_with_mode(
                empty,
                0,
                False,
                IBus.PreeditFocusMode.COMMIT,
            )


def run(layout: ParsedLayout, engine_name: str, x_display: str) -> None:
    """Serve the keyboard to ibus-daemon until it quits.

    Args:
        layout: The parsed layout.
        engine_name: The engine name, as in the IBus component file.
        x_display: The X display of the clients that get key presses, for
            example ":0".

    Raises:
        ConnectionError: If ibus-daemon is not running.
    """
    IBus.init()
    bus = IBus.Bus()
    if not bus.is_connected():
        raise ConnectionError("cannot connect to ibus-daemon; is it running?")
    bus.connect("disconnected", lambda _bus: IBus.quit())
    # One X typer for all instances, opened on first use. python3-xlib is
    # needed only for it: without it, every client gets IBus text.
    try:
        from gujarati_phonetic.io.x_typer import XTyper

        typer: XTyper | None = XTyper(x_display)
    except ImportError:
        typer = None
    connection = bus.get_connection()
    factory = IBus.Factory.new(connection)
    # The instances, kept alive here, and the numbers of their object paths.
    engines: list[GujaratiPhoneticEngine] = []
    numbers = count(1)

    # IBus asks for an instance per input context; created here rather than by
    # add_engine, to set has_focus_id.
    def create_engine(
        _factory: IBus.Factory,
        name: str,
    ) -> GujaratiPhoneticEngine | None:
        engine = None
        if name == engine_name:
            object_path = f"/org/freedesktop/IBus/Engine/{next(numbers)}"
            engine = GujaratiPhoneticEngine(
                engine_name,
                object_path,
                connection,
                layout,
                typer,
            )
            engines.append(engine)
        return engine

    factory.connect("create-engine", create_engine)
    # The bus name of the IBus component file (packaging/gujarati-phonetic.xml).
    bus.request_name("org.freedesktop.IBus.GujaratiPhonetic", 0)
    IBus.main()
    # Give the spare key codes back to the X display.
    if typer is not None:
        try:
            typer.close()
        except ConnectionError:
            pass
