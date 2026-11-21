"""gujarati-phonetic-check: type a test word through the installed keyboard."""

from __future__ import annotations

import argparse
import sys

from gujarati_phonetic import __version__


def main(argv: list[str] | None = None) -> None:
    """Type keys through ibus-daemon and print the text an application gets.

    Args:
        argv: Command line arguments, sys.argv[1:] if None.
    """
    parser = argparse.ArgumentParser(
        prog="gujarati-phonetic-check",
        description=(
            "Check the installation: type keys through ibus-daemon with the "
            "Gujarati phonetic keyboard and print the result."
        ),
    )
    parser.add_argument(
        "keys", nargs="?", default="kem Cho", help="keys to type (default: kem Cho)"
    )
    parser.add_argument(
        "--engine",
        default="gujarati-phonetic",
        help="IBus engine to type with (default: %(default)s)",
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        # IBus is only on the target system.
        from gujarati_phonetic.io import ibus_client

        text = ibus_client.type_through_ibus(args.engine, args.keys)
    except (ConnectionError, LookupError, ImportError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    print(text)
