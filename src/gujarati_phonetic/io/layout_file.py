"""Read the layout data file."""

from __future__ import annotations

import json
from pathlib import Path

from gujarati_phonetic.schema.layout import LayoutInput


def default_layout_file() -> Path:
    """Return the Gujarati phonetic layout shipped with the package.

    The package is installed as plain files (packaging/install.sh), so the
    data file is found next to the modules, the same on every Python version.

    Returns:
        The packaged data/gu_phone.json, generated from Google's gu_phone.js.
    """
    package = Path(__file__).resolve().parent.parent
    return package / "data" / "gu_phone.json"


def read_layout(path: Path) -> LayoutInput:
    """Read a layout data file.

    Args:
        path: The JSON file written by scripts/google_oracle.mjs.

    Returns:
        The layout.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the file is not valid JSON or not a layout.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    match data:
        case {
            "id": str(layout_id),
            "title": str(title),
            "mappings": dict(mappings),
            "transforms": list(transforms),
            "history_prune_regex": str(history_prune_regex),
        }:
            layout = LayoutInput(
                layout_id=layout_id,
                title=title,
                mappings=mappings,
                transforms=[(str(pattern), str(repl)) for pattern, repl in transforms],
                history_prune_regex=history_prune_regex,
            )
        case _:
            raise ValueError(f"{path}: not a keyboard layout file")
    return layout
