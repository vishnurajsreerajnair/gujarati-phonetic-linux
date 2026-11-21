"""Desktop notifications: ChromeOS shows those of the Linux apps."""

from __future__ import annotations

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


def notify(summary: str, body: str) -> None:
    """Show a short notification, through the freedesktop notification service.

    Args:
        summary: The title.
        body: The text under the title.

    Raises:
        ConnectionError: If no notification service answers.
    """
    # Notify(app_name, replaces_id, icon, summary, body, actions, hints,
    # timeout in ms); transient: not kept in the notification list.
    arguments = GLib.Variant(
        "(susssasa{sv}i)",
        (
            "Gujarati keyboard",
            0,
            "gujarati-phonetic",
            summary,
            body,
            [],
            {"transient": GLib.Variant("b", True)},
            3000,
        ),
    )
    try:
        session = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        session.call_sync(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications",
            "org.freedesktop.Notifications",
            "Notify",
            arguments,
            GLib.VariantType.new("(u)"),
            Gio.DBusCallFlags.NONE,
            2000,
            None,
        )
    except GLib.Error as error:
        raise ConnectionError(f"no notification service: {error.message}") from error
