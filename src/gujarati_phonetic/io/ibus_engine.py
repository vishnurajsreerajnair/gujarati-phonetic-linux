"""The IBus input method engine: connects the keyboard to Linux applications."""

from __future__ import annotations

from itertools import count
from typing import TYPE_CHECKING

import gi

gi.require_version("IBus", "1.0")
from gi.repository import Gio, GLib, IBus

from gujarati_phonetic.core.keys import KeyAction, classify_key
from gujarati_phonetic.core.screen import needs_key_presses, screen_edit
from gujarati_phonetic.models.composer import BACKSPACE, Composer, KeyResult
from gujarati_phonetic.models.parsed_layout import ParsedLayout
from gujarati_phonetic.models.switch import LanguageSwitch

if TYPE_CHECKING:
    from gujarati_phonetic.io.x_typer import XTyper


class GujaratiPhoneticEngine(IBus.Engine):
    """One keyboard instance, created by run() for each IBus input context.

    Args:
        engine_name: The engine name, as in the IBus component file.
        object_path: The D-Bus object path of the instance.
        connection: The connection to ibus-daemon.
        layout: The parsed layout.
        switch: The language, shared by all instances.
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
        switch: LanguageSwitch,
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
        self.switch = switch
        self.typer = typer
        # Key presses mode: the composition is typed in the document, as
        # `shown`, instead of being sent to the client.
        self.key_presses = False
        self.shown = ""
        # Whether a timer will send the waiting key presses.
        self.sending = False

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
        released = bool(state & IBus.ModifierType.RELEASE_MASK)
        if own_key and not released and self.typer is not None:
            # The application has read this press.
            self.typer.read(keycode + 8)
        if not own_key and not released:
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
            modifiers = (
                IBus.KEY_Shift_L,
                IBus.KEY_Shift_R,
                IBus.KEY_Control_L,
                IBus.KEY_Control_R,
                IBus.KEY_Alt_L,
                IBus.KEY_Alt_R,
                IBus.KEY_Caps_Lock,
                IBus.KEY_Super_L,
                IBus.KEY_Super_R,
                IBus.KEY_Meta_L,
                IBus.KEY_Meta_R,
                IBus.KEY_Hyper_L,
                IBus.KEY_Hyper_R,
                IBus.KEY_ISO_Level3_Shift,
            )
            action = classify_key(
                char,
                is_space,
                keyval == IBus.KEY_BackSpace,
                keyval in modifiers,
                bool(state & IBus.ModifierType.CONTROL_MASK),
                bool(state & IBus.ModifierType.MOD1_MASK),
                bool(state & meta),
            )
            match action:
                case KeyAction.TOGGLE:
                    self.finish_word()
                    self.switch.flip()
                    handled = True
                case _ if not self.switch.gujarati:
                    handled = False
                case KeyAction.TYPE:
                    key = " " if is_space else char
                    handled = self._show(self.composer.type_key(key))
                case KeyAction.BACKSPACE:
                    handled = self._show(self.composer.type_key(BACKSPACE))
                case KeyAction.MODIFIER:
                    handled = False
                case KeyAction.PASS:
                    self.finish_word()
                    handled = False
            # In key presses mode a key for the application must not overtake
            # the presses still on their way: it goes after them.
            shortcut = (
                IBus.ModifierType.CONTROL_MASK | IBus.ModifierType.MOD1_MASK | meta
            )
            typer = self.typer if self.key_presses else None
            if (
                typer is not None
                and not handled
                and not state & shortcut
                and action not in (KeyAction.MODIFIER, KeyAction.TOGGLE)
                and typer.busy()
            ):
                typer.type_key(keyval, keycode + 8, char)
                handled = True
                if not self.sending:
                    self._send()
        return handled

    def do_focus_in_id(self, object_path: str, client: str) -> None:
        """Choose how to give the text to the client that gets the focus.

        Args:
            object_path: The input context (unused).
            client: The client name.
        """
        self.key_presses = (
            needs_key_presses(client) and self.typer is not None and self.typer.ready()
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
        self.finish_word()

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
            self.typer.type_text(backspaces, chars)
            self.shown = result.composition
            # A timer already set sends these keys after the earlier ones.
            if not self.sending:
                self._send()
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

    def _send(self) -> bool:
        """Press the waiting keys, and set a timer for those that must wait.

        Returns:
            False, for GLib: a timer that calls this method runs once.
        """
        self.sending = False
        # The keys typed before a focus change still go: as real keys would,
        # they reach the window that has the focus (a spreadsheet's next cell).
        if self.typer is not None:
            try:
                delay = self.typer.send()
            except ConnectionError:
                # The display is gone: IBus text from the next key on.
                self.key_presses = False
                delay = None
            if delay is not None:
                self.sending = True
                GLib.timeout_add(delay, self._send)
        return False

    def finish_word(self) -> None:
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
    # The live instances, kept alive here, and the numbers of their object paths.
    engines: list[GujaratiPhoneticEngine] = []
    numbers = count(1)
    switch = LanguageSwitch()

    def forget_engine(engine: GujaratiPhoneticEngine) -> None:
        engines.remove(engine)

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
                switch,
                typer,
            )
            engines.append(engine)
            # IBus destroys the instance when its input context closes.
            engine.connect("destroy", forget_engine)
        return engine

    factory.connect("create-engine", create_engine)

    # The shelf toggle (gujarati-phonetic-toggle) switches the language with
    # the Toggle method, that returns the language now on.
    introspection = """<node>
      <interface name="org.freedesktop.IBus.GujaratiPhonetic.Language">
        <method name="Toggle">
          <arg type="s" name="language" direction="out"/>
        </method>
      </interface>
    </node>"""
    node = Gio.DBusNodeInfo.new_for_xml(introspection)

    def toggle(
        _connection: Gio.DBusConnection,
        _sender: str,
        _object_path: str,
        _interface_name: str,
        _method_name: str,
        _parameters: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ) -> None:
        for engine in engines:
            engine.finish_word()
        gujarati = switch.flip()
        language = "gujarati" if gujarati else "english"
        invocation.return_value(GLib.Variant("(s)", (language,)))

    connection.register_object(
        "/org/freedesktop/IBus/GujaratiPhonetic",
        node.interfaces[0],
        toggle,
        None,
        None,
    )
    # The bus name of the IBus component file (packaging/gujarati-phonetic.xml).
    bus.request_name("org.freedesktop.IBus.GujaratiPhonetic", 0)
    IBus.main()
    # Give the spare key codes back to the X display.
    if typer is not None:
        try:
            typer.close()
        except ConnectionError:
            pass
