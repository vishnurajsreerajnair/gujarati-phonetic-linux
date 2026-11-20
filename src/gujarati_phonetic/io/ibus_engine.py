"""The IBus input method engine: connects the keyboard to Linux applications."""

from __future__ import annotations

import gi

gi.require_version("IBus", "1.0")
from gi.repository import GObject, IBus

from gujarati_phonetic.core.keys import KeyAction, classify_key
from gujarati_phonetic.models.composer import BACKSPACE, Composer, KeyResult
from gujarati_phonetic.models.parsed_layout import ParsedLayout

# Must match packaging/gujarati-phonetic.xml.
ENGINE_NAME = "gujarati-phonetic"
BUS_NAME = "org.freedesktop.IBus.GujaratiPhonetic"
META_MASKS = (
    IBus.ModifierType.SUPER_MASK
    | IBus.ModifierType.META_MASK
    | IBus.ModifierType.HYPER_MASK
    | IBus.ModifierType.MOD4_MASK
)


class GujaratiPhoneticEngine(IBus.Engine):
    """One keyboard instance, created by IBus for each input context.

    Attributes:
        layout: The parsed layout shared by all instances; set by run() before
            IBus creates any.
    """

    __gtype_name__ = "GujaratiPhoneticEngine"
    layout: ParsedLayout

    def __init__(self) -> None:
        super().__init__()
        self.composer = Composer(self.layout)
        self.gujarati = True

    def do_process_key_event(self, keyval: int, keycode: int, state: int) -> bool:
        """Handle a key press.

        Args:
            keyval: The X key symbol.
            keycode: The hardware key code (unused).
            state: The modifier mask.

        Returns:
            Whether the key was used; if not, the application gets it.
        """
        handled = False
        if not state & IBus.ModifierType.RELEASE_MASK:
            code = IBus.keyval_to_unicode(keyval)
            is_space = keyval == IBus.KEY_space
            action = classify_key(
                chr(code) if code else "",
                is_space,
                keyval == IBus.KEY_BackSpace,
                bool(state & IBus.ModifierType.CONTROL_MASK),
                bool(state & IBus.ModifierType.MOD1_MASK),
                bool(state & META_MASKS),
            )
            match action:
                case KeyAction.TOGGLE:
                    self._finish_word()
                    self.gujarati = not self.gujarati
                    handled = True
                case _ if not self.gujarati:
                    handled = False
                case KeyAction.TYPE:
                    key = " " if is_space else chr(code)
                    handled = self._show(self.composer.type_key(key))
                case KeyAction.BACKSPACE:
                    handled = self._show(self.composer.type_key(BACKSPACE))
                case KeyAction.PASS:
                    self._finish_word()
                    handled = False
        return handled

    def do_focus_out(self) -> None:
        """Forget the word; IBus commits the composition itself (commit mode)."""
        self.composer.reset()

    def do_reset(self) -> None:
        """Forget the word; IBus commits the composition itself (commit mode)."""
        self.composer.reset()

    def do_disable(self) -> None:
        """Finish the word when the keyboard is switched off."""
        self._finish_word()

    def _show(self, result: KeyResult) -> bool:
        """Commit text and show the composition.

        Args:
            result: The result of a key.

        Returns:
            Whether the key was used.
        """
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
        if text:
            self.commit_text(IBus.Text.new_from_string(text))
        self.update_preedit_text_with_mode(
            IBus.Text.new_from_string(""), 0, False, IBus.PreeditFocusMode.COMMIT
        )


def run(layout: ParsedLayout) -> None:
    """Serve the keyboard to ibus-daemon until it quits.

    Args:
        layout: The parsed layout.

    Raises:
        ConnectionError: If ibus-daemon is not running.
    """
    IBus.init()
    bus = IBus.Bus()
    if not bus.is_connected():
        raise ConnectionError("cannot connect to ibus-daemon; is it running?")
    bus.connect("disconnected", lambda _bus: IBus.quit())
    GujaratiPhoneticEngine.layout = layout
    factory = IBus.Factory.new(bus.get_connection())
    engine_type = GObject.type_from_name(GujaratiPhoneticEngine.__gtype_name__)
    factory.add_engine(ENGINE_NAME, engine_type)
    bus.request_name(BUS_NAME, 0)
    IBus.main()
