"""The Python port types exactly what Google's ChromeOS engine types."""

from __future__ import annotations

from gujarati_phonetic.models.composer import Composer
from gujarati_phonetic.models.parsed_layout import ParsedLayout


def test_every_reference_sequence_matches_google(
    layout: ParsedLayout, google_cases: list[dict[str, object]]
) -> None:
    """Each key commits and composes the same text as Google's engine."""
    differences = []
    for case in google_cases:
        keys = str(case["keys"])
        composer = Composer(layout)
        steps: list[list[object]] = []
        for key in keys:
            result = composer.type_key(key)
            steps.append([result.handled, result.commit, result.composition])
        steps.append([True, composer.reset(), composer.composition])
        if steps != case["steps"]:
            differences.append((keys, case["steps"], steps))
    assert len(google_cases) > 40000
    assert differences[:3] == []
