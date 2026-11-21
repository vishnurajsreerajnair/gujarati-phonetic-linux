# Changelog

## [Unreleased]

- Gujarati phonetic keyboard for Linux apps (IBus), typing exactly as Google's ChromeOS Gujarati Phonetic keyboard.
- Ctrl+Space or Alt+Space switches between Gujarati and English.
- Consonant + `y` now gives the ય conjunct (વિદ્યાર્થી); `Y` gives ય઼ (fix of Google's layout).
- `gujarati-phonetic-check` types a test word through the installed keyboard.
- Install and uninstall scripts for the Linux of a Chromebook.
- Gujarati typing in ONLYOFFICE documents and spreadsheets, which drop input method text: the keyboard types the letters there as key presses, also when typing fast.
- Runs on Python 3.10 and later.
- `gujarati-phonetic-toggle` and the shelf app "ગુજરાતી / English": one click switches between Gujarati and English and shows the language in a notification.
- One language for all apps: switching in one window switches every window, as on ChromeOS.
- Shift, Ctrl, Alt or Caps Lock pressed alone no longer ends the word: `vidyArthI` gives વિદ્યાર્થી.
- Fast typing in LibreOffice keeps the order of the letters (IBus sync mode).
- The shelf app shows the language in a small window where Linux has no notification service.
- A guide in Gujarati with pictures (`docs/guide-gu.md`); the installer puts it as a PDF in Linux files.
- `--engine` option of `gujarati-phonetic-engine` and `gujarati-phonetic-check`: the IBus engine name.
