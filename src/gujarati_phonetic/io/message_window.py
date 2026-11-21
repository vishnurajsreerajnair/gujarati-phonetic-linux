"""A small window with a message, that closes by itself.

For Linux systems without a notification service (the Linux of a Chromebook
without cros-notificationd).
"""

from __future__ import annotations

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk


def show_message(summary: str, body: str, milliseconds: int) -> None:
    """Show a message in a small window, and close it after a time.

    The window does not take the keyboard focus, so that typing goes on in
    the document.

    Args:
        summary: The title, in large letters.
        body: The text under the title.
        milliseconds: How long the window stays.

    Raises:
        ConnectionError: If there is no display to show the window on.
    """
    ready, _ = Gtk.init_check(None)
    if not ready:
        raise ConnectionError("no display for the message window")
    window = Gtk.Window(title=summary)
    window.set_decorated(False)
    window.set_accept_focus(False)
    window.set_focus_on_map(False)
    window.set_keep_above(True)
    window.set_type_hint(Gdk.WindowTypeHint.NOTIFICATION)
    window.set_position(Gtk.WindowPosition.CENTER)
    title = Gtk.Label()
    title.set_markup(f"<span size='xx-large' weight='bold'>{summary}</span>")
    text = Gtk.Label(label=body)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    box.set_border_width(24)
    box.pack_start(title, False, False, 0)
    box.pack_start(text, False, False, 0)
    window.add(box)
    window.show_all()
    GLib.timeout_add(milliseconds, Gtk.main_quit)
    Gtk.main()
    window.destroy()
