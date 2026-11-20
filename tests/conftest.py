"""Shared fixtures."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from gujarati_phonetic.io.layout_file import default_layout_file, read_layout
from gujarati_phonetic.models.parsed_layout import ParsedLayout

DATA = Path(__file__).parent / "data"
ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def layout() -> ParsedLayout:
    """The packaged Gujarati phonetic layout, parsed."""
    return ParsedLayout(read_layout(default_layout_file()))


@pytest.fixture(scope="session")
def google_cases() -> list[dict[str, object]]:
    """Google's engine on every reference sequence (scripts/google_oracle.mjs).

    Each case has "keys" (the typed characters, "\\b" for Backspace) and
    "steps": per key [handled, committed, composition], then a final reset.
    """
    with gzip.open(DATA / "google_oracle.json.gz", "rt", encoding="utf-8") as file:
        cases: list[dict[str, object]] = json.load(file)
    return cases


@pytest.fixture(scope="session")
def root() -> Path:
    """The repository root."""
    return ROOT
