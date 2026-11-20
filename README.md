# gujarati-phonetic-linux

Type Gujarati by sound in Linux desktop apps (LibreOffice and other GTK apps),
exactly as with the **Gujarati Phonetic** keyboard of ChromeOS:
`kem Cho` gives **કેમ છો**.

ChromeOS's own Gujarati keyboard does not reach the Linux apps of a
Chromebook. This package brings the same engine and the same rules to Linux,
as an IBus input method. The engine is a Python port of Google's ChromeOS
keyboard code (google-input-tools, Apache 2.0). It is tested to commit and
show the same text as Google's code, key by key, on 41,792 typed sequences.

## Install (Linux on a Chromebook, or Debian/Ubuntu)

In the Linux Terminal:

```sh
curl --location https://github.com/vishnurajsreerajnair/gujarati-phonetic-linux/archive/refs/heads/main.tar.gz | tar xz
cd gujarati-phonetic-linux-main
sh packaging/install.sh
```

Then restart Linux: right-click the Terminal icon, **Shut down Linux**, and
open the app again. To check the keyboard, run this in the Terminal:

```sh
gujarati-phonetic-check "kem Cho"
```

It prints `કેમ છો`.

`install.sh` does the following:

- Installs IBus with its Python bindings.
- Copies the keyboard to `/usr/lib/gujarati-phonetic-linux`.
- Makes IBus the input method of the Linux apps (`~/.config/environment.d/ibus.conf`). This replaces fcitx5 if it was set up.
- Starts IBus with this keyboard when Linux starts (`~/.sommelierrc`).

To remove it, run `sh packaging/uninstall.sh`.

## Typing

The keyboard starts in Gujarati. **Ctrl+Space** or **Alt+Space** switches
between Gujarati and English.

The word being typed is underlined and may still change: `k` gives ક, then
`a` gives કા. Space, a punctuation key or a click commits it.

| Keys | Gujarati | Keys | Gujarati |
|---|---|---|---|
| `a A i I u U` | અ આ ઇ ઈ ઉ ઊ | `e ai o au` | એ ઐ ઓ ઔ |
| `k kh g gh ~N` | ક ખ ગ ઘ ઙ | `ch Ch j jh ~n` | ચ છ જ ઝ ઞ |
| `T Th D Dh N` | ટ ઠ ડ ઢ ણ | `t th d dh n` | ત થ દ ધ ન |
| `p ph b bh m` | પ ફ બ ભ મ | `y r l L v` | ય ર લ ળ વ |
| `sh Sh s h` | શ ષ સ હ | `x j~n` | ક્ષ જ્ઞ |
| `M .n` | ં (anusvara) | `.N` | ઁ (candrabindu) |
| `H` | ઃ (visarga) | `R^i` | ઋ |

Consonants join on their own: `kk` gives ક્ક and `vidyArthI` gives
વિદ્યાર્થી. Long vowels can be typed doubled: `gujaraatii` gives ગુજરાતી.

## How it works

`third_party/google-input-tools/` holds Google's original files, unchanged.
`scripts/google_oracle.mjs` runs them in Node and writes two files:

- `src/gujarati_phonetic/data/gu_phone.json`: the layout's 210 rules, as data.
- `tests/data/google_oracle.json.gz`: what Google's engine commits and shows after each key of 41,792 sequences. These are all the 95 keys, all pairs and triples of the phonetic keys, common words with Space and Backspace, and random typing.

The Python package (`src/gujarati_phonetic/`) has these parts:

| Module | Port of |
|---|---|
| `models/parsed_layout.py` | `parsedlayout.js`: the rules, matched at the end of the text |
| `models/model.py` | `model.js`: the history that lets a later key change earlier letters |
| `models/composer.py` | `composetextinput.js` and the key step of `controller.js`: what to commit and what to keep underlined |
| `core/` | JavaScript regular expression behaviour and the combining marks |
| `io/ibus_engine.py` | (new) the IBus engine |
| `io/ibus_client.py` | (new) the installation check |

`tests/lib/test_google_parity.py` replays every reference sequence and
requires the same result as Google's engine at every key.

### Fix of Google's layout

In Google's `gu_phone.js`, the rules for a consonant followed by `y` are
commented out. The nukta rules after them were written with a lowercase `y`
where the key of every other nukta letter is capital (`R q G z J f Y`). As a
result, `vidyArthI` gave વિદ્ય઼આર્થી, and વિદ્યાર્થી could not be typed. The
generator splits each of these three rules into two: `y` gives ય and `Y`
gives ય઼. The reference data is produced with the fixed rules, so the
port still matches Google's engine.

## Development

```sh
python -m venv ~/virtualenv/gujarati-phonetic
~/virtualenv/gujarati-phonetic/bin/pip install pytest mypy ruff black
~/virtualenv/gujarati-phonetic/bin/python -m pytest
node scripts/google_oracle.mjs   # regenerate the layout and the reference data
```

The package has no dependencies besides Python 3.11+. The IBus modules need
`python3-gi` and `gir1.2-ibus-1.0` and are not imported by the tests.

## License

Apache License 2.0; see `LICENSE` and `NOTICE`. The engine and the layout are
derived from google-input-tools, Copyright 2013 The ChromeOS IME Authors.
