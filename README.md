# gujarati-phonetic-linux

Type Gujarati by sound in the Linux apps of a Chromebook (LibreOffice,
ONLYOFFICE and other desktop apps), exactly as with the **Gujarati Phonetic**
keyboard of ChromeOS: `kem Cho` gives **કેમ છો**.

## The problem

- **ChromeOS keyboards do not reach Linux apps.** The Gujarati keyboards of
  ChromeOS work in Chrome and Android apps, but not in the Linux apps of a
  Chromebook (Crostini): Google's bridge for them (cros-im) is not available
  for the current Debian. Linux apps get plain English keys.
- **The Linux Gujarati keyboards type differently.** Linux has phonetic
  Gujarati keyboards (m17n, ITRANS), but their rules differ from Google's, and
  someone used to the ChromeOS keyboard types wrong words with them.
- **ONLYOFFICE drops the text of input methods.** Its Linux app bundles an old
  Qt (5.9), which loses all the text that an input method sends: nothing
  appears. This is an [open ONLYOFFICE bug](https://community.onlyoffice.com/t/keyboard-input-methods-don-t-work-on-linux-applications-of-onlyoffice/10752).

This package is Google's ChromeOS Gujarati Phonetic keyboard for Linux: the
same engine and the same rules, as an IBus input method. The engine is a Python
port of Google's code (google-input-tools, Apache 2.0), tested to give the same
text as Google's code, key by key, on 41,792 typed sequences.

## What is installed, and why

| Part | Why it is needed |
|---|---|
| The keyboard engine (`/usr/lib/gujarati-phonetic-linux`) | Google's rules, typed into any Linux app through IBus. |
| IBus (`ibus`, `ibus-gtk3`, `python3-gi`, `gir1.2-ibus-1.0`) | The Linux input method framework that apps talk to. |
| `~/.config/environment.d/ibus.conf` | Tells the Linux apps to use IBus (`GTK_IM_MODULE`, `QT_IM_MODULE`, `XMODIFIERS`). Replaces fcitx5 if it was set up. |
| The systemd user service `gujarati-phonetic-ibus` | Starts IBus with this keyboard when Linux starts. |
| One fixed IBus address (`IBUS_ADDRESS`, also in `~/.bashrc`) | ChromeOS runs several displays (X `:0`, X `:1`, Wayland), and IBus would look for a separate daemon on each one; with one address, every app finds the same keyboard. |
| `python3-xlib` | For ONLYOFFICE only: the keyboard types the letters there as key presses (see below). |
| `x11-xkb-utils` | `setxkbmap`, which IBus uses to set the key layout. |

### ONLYOFFICE: key presses

ONLYOFFICE drops the text of input methods but reads normal key presses. When
a Qt app (IBus client `QIBusInputContext`) has the focus, the keyboard
therefore types each Gujarati letter as a simulated key press (XTest), on a
spare key code of the X display mapped to that letter, and corrects a letter
with Backspace when a later key changes it (`s` gives સ, then `h` turns it
into શ). This is a workaround for the ONLYOFFICE bug, not a fix: it stops being
needed when ONLYOFFICE handles input methods. The X display is `:0`
(`gujarati-phonetic-engine --x-display`).

## Install

In the Linux Terminal:

```sh
curl --location https://github.com/vishnurajsreerajnair/gujarati-phonetic-linux/archive/refs/heads/main.tar.gz | tar xz
cd gujarati-phonetic-linux-main
sh packaging/install.sh
```

Restart Linux (right-click the Terminal icon, **Shut down Linux**), then check
the keyboard in the Terminal:

```sh
gujarati-phonetic-check "kem Cho"
```

It prints `કેમ છો`. To remove everything: `sh packaging/uninstall.sh`.

## Controls

- **ChromeOS keyboard: US.** The keyboard indicator at the bottom right of the
  screen must say **US** while typing in Linux apps. With a ChromeOS Gujarati
  keyboard (GU, BK) the keys are changed before Linux sees them.
- **Ctrl+Space** or **Alt+Space**: switch between Gujarati and English. The
  keyboard starts in Gujarati.
- The word being typed may still change: `k` gives ક, then `a` gives કા.
  Space, Enter, a punctuation key or an arrow key finishes it. In LibreOffice
  it is underlined while it can change; in ONLYOFFICE it is not.
- Shortcuts with Ctrl, Alt or Search (Ctrl+S, Ctrl+C, ...) go to the app as
  usual.
- **Backspace** while typing a word changes the word (`kemm` then Backspace
  gives કેમ); otherwise it deletes as usual.

## Key map

Generated from the engine. Capital letters are typed with Shift.

**Vowels** (at the start of a word) and **vowel signs** (after a consonant,
shown with ક):

| Keys | Vowel | Sign | Keys | Vowel | Sign |
|---|---|---|---|---|---|
| `a` | અ | ક | `e` | એ | કે |
| `aa` or `A` | આ | કા | `ai` | ઐ | કૈ |
| `i` | ઇ | કિ | `o` | ઓ | કો |
| `ii` or `I` | ઈ | કી | `au` | ઔ | કૌ |
| `u` | ઉ | કુ | `R^i` | ઋ | |
| `uu` or `U` | ઊ | કૂ | `R^I` | ૠ | |

**Consonants**:

| Keys | | Keys | | Keys | | Keys | | Keys | |
|---|---|---|---|---|---|---|---|---|---|
| `k` | ક | `kh` | ખ | `g` | ગ | `gh` | ઘ | `~N` | ઙ |
| `ch` | ચ | `Ch` | છ | `j` | જ | `jh` | ઝ | `~n` | ઞ |
| `T` | ટ | `Th` | ઠ | `D` | ડ | `Dh` | ઢ | `N` | ણ |
| `t` | ત | `th` | થ | `d` | દ | `dh` | ધ | `n` | ન |
| `p` | પ | `ph` | ફ | `b` | બ | `bh` | ભ | `m` | મ |
| `y` | ય | `r` | ર | `l` | લ | `L` | ળ | `v` or `w` | વ |
| `sh` | શ | `Sh` | ષ | `s` | સ | `h` | હ | | |
| `x` or `kSh` | ક્ષ | `j~n` or `GY` | જ્ઞ | | | | | | |

**With nukta**: `q` ક઼, `Kh` ખ઼, `G` ગ઼, `z` or `J` જ઼, `.D` ડ઼, `Rh` ઢ઼,
`f` ફ઼, `Y` ય઼, `R` ર઼.

**Signs**: `M` or `.n` ં (anusvara, કં), `.N` ઁ (candrabindu, કઁ), `H` ઃ
(visarga, કઃ), `.h` ્ (visible virama, ક્), `OM` ૐ.

**Joined consonants** form on their own: `kk` ક્ક, `tr` ત્ર, `shrI` શ્રી,
`dharma` ધર્મ, `chandra` ચન્દ્ર, `kShetra` ક્ષેત્ર, `vidyArthI` વિદ્યાર્થી.

Digits and punctuation stay as typed: `0`–`9`, `.`, `,`, `?` (Google's layout
has no Gujarati digits and no ।).

## Known issues

- **ૃ cannot be typed** (કૃષ્ણ, હૃદય, દૃષ્ટિ). Google's layout has rules for
  it that can never match: `kRRi` gives ક્ર઼ર઼ઇ and `kR^i` gives ક્ઋ, in
  Google's own engine too.
- **ONLYOFFICE, clicking inside a word**: the keyboard does not see mouse
  clicks. If the word being typed can still change (for example after `s`,
  which `h` can turn into શ) and you click elsewhere, the next key may correct
  the letter at the new place. Press Space or an arrow key before clicking.
- **Ctrl+Space and Alt+Space** were not tested through Chrome Remote Desktop,
  which drops modifier keys.

## How it works

`third_party/google-input-tools/` holds Google's original files, unchanged.
`scripts/google_oracle.mjs` runs them in Node and writes two files:

- `src/gujarati_phonetic/data/gu_phone.json`: the layout's 210 rules, as data.
- `tests/data/google_oracle.json.gz`: what Google's engine commits and shows
  after each key of 41,792 sequences. These are all the 95 keys, all pairs and
  triples of the phonetic keys, common words with Space and Backspace, and
  random typing.

The Python package (`src/gujarati_phonetic/`) has these parts:

| Module | What it does |
|---|---|
| `models/parsed_layout.py` | Port of `parsedlayout.js`: the rules, matched at the end of the text |
| `models/model.py` | Port of `model.js`: the history that lets a later key change earlier letters |
| `models/composer.py` | Port of `composetextinput.js` and the key step of `controller.js`: what to commit and what can still change |
| `core/` | JavaScript regular expression behaviour, the combining marks, the keys, and the key presses that change the text on screen |
| `io/ibus_engine.py` | The IBus engine |
| `io/x_typer.py` | The key presses for ONLYOFFICE (XTest) |
| `io/ibus_client.py` | The installation check |

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
~/virtualenv/gujarati-phonetic/bin/pip install -e '.[dev]'
~/virtualenv/gujarati-phonetic/bin/python -m pytest
node scripts/google_oracle.mjs   # regenerate the layout and the reference data
```

Python 3.10 or later (tested on 3.10, 3.13 and 3.14). The engine itself needs
only the standard library; IBus needs `python3-gi` and `gir1.2-ibus-1.0`, and
the ONLYOFFICE key presses need `python3-xlib`. The tests do not import the
IBus modules and use a fake X display.

## License

Apache License 2.0; see `LICENSE` and `NOTICE`. The engine and the layout are
derived from google-input-tools, Copyright 2013 The ChromeOS IME Authors.
