# Changelog

## [Unreleased]

## [1.0.0] - 2026-11-21

- Gujarati phonetic keyboard for the Linux apps of a Chromebook (IBus), typing exactly as Google's ChromeOS Gujarati Phonetic keyboard.
- Consonant + `y` gives the ય conjunct (વિદ્યાર્થી); `Y` gives ય઼ (fix of Google's layout).
- Gujarati in ONLYOFFICE documents and spreadsheets, which drop input method text: the keyboard types the letters there as key presses, also when typing fast.
- Fast typing in LibreOffice keeps the letters in order (IBus sync mode).
- Shift, Ctrl, Alt or Caps Lock pressed alone does not end the word.
- The shelf app "ગુજરાતી / English" (`gujarati-phonetic-toggle`) and Ctrl+Space or Alt+Space switch between Gujarati and English, in every window at once; the app shows the language in a notification, or in a small window where Linux has none.
- A guide in Gujarati with pictures (`docs/guide-gu.md`), installed as a PDF in Linux files.
- `gujarati-phonetic-check` types a test word through the installed keyboard; `--engine` sets the IBus engine name.
- Install and uninstall scripts for the Linux of a Chromebook.
- Runs on Python 3.10 and later.
