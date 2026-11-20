"""gujarati-phonetic-engine: the IBus engine process, started by ibus-daemon."""

from __future__ import annotations

import argparse
import re
import sys

from gujarati_phonetic import __version__
from gujarati_phonetic.io.layout_file import default_layout_file, read_layout
from gujarati_phonetic.models.parsed_layout import ParsedLayout


def main(argv: list[str] | None = None) -> None:
    """Run the Gujarati phonetic IBus engine.

    Args:
        argv: Command line arguments, sys.argv[1:] if None.
    """
    parser = argparse.ArgumentParser(
        prog="gujarati-phonetic-engine",
        description=(
            "Gujarati phonetic keyboard for IBus (Google ChromeOS rules). "
            "ibus-daemon starts it; it is not meant to be run by hand."
        ),
    )
    parser.add_argument("--ibus", action="store_true", help="accepted from ibus-daemon")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    try:
        layout = ParsedLayout(read_layout(default_layout_file()))
        # IBus is only on the target system; import it after the layout check.
        from gujarati_phonetic.io import ibus_engine

        ibus_engine.run(layout)
    except (OSError, ValueError, re.error, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
