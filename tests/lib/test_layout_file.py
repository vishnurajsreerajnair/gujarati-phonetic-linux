"""Reading the layout data file."""

from __future__ import annotations

from pathlib import Path

import pytest

from gujarati_phonetic.io.layout_file import default_layout_file, read_layout


def test_packaged_layout() -> None:
    """The packaged layout is Google's gu_phone, with the fixed y rules."""
    layout = read_layout(default_layout_file())
    assert layout.layout_id == "gu_phone"
    # Google's 207 rules, three of them split into a "y" and a "Y" rule.
    assert len(layout.transforms) == 210
    assert ("([ક-હ])\x1dy", "$1્ય") in layout.transforms


def test_not_a_layout(tmp_path: Path) -> None:
    """A JSON file of another shape is refused."""
    path = tmp_path / "other.json"
    path.write_text('{"id": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="not a keyboard layout"):
        read_layout(path)
