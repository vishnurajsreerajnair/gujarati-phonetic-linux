"""gujarati-phonetic-toggle: switch between Gujarati and English (shelf icon)."""

from __future__ import annotations

import argparse
import sys

from gujarati_phonetic import __version__


def main(argv: list[str] | None = None) -> None:
    """Switch the keyboard language, print it and show it on screen.

    The language goes in a notification, or in a small window that closes by
    itself where no notification service runs.

    Args:
        argv: Command line arguments, sys.argv[1:] if None.
    """
    parser = argparse.ArgumentParser(
        prog="gujarati-phonetic-toggle",
        description=(
            "Switch the keyboard of the Linux apps between Gujarati and English, "
            "and show the language now on in a notification."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    try:
        # IBus is only on the target system.
        from gujarati_phonetic.io import ibus_client

        language = ibus_client.toggle_language()
    except (ConnectionError, ImportError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    print(language)
    if language == "gujarati":
        summary = "ગુજરાતી"
        body = "The keyboard types Gujarati: kem Cho gives કેમ છો."
    else:
        summary = "English"
        body = "The keyboard types English."
    try:
        from gujarati_phonetic.io import notification

        notification.notify(summary, body)
    except (ConnectionError, ImportError, ValueError):
        # No notification service (a Chromebook's Linux without
        # cros-notificationd): a small window instead.
        try:
            from gujarati_phonetic.io import message_window

            message_window.show_message(summary, body, 2000)
        except (ConnectionError, ImportError, ValueError) as error:
            print(f"Error: {error}", file=sys.stderr)
            sys.exit(1)
