# google-input-tools (copy)

Unchanged files from <https://github.com/google/google-input-tools>, commit
`fc9f11d80d957560f7accf85a5fc27dd23625f70` (the project is archived), under
the Apache License 2.0 (`LICENSE`).

| File | Upstream path |
|---|---|
| `gu_phone.js` | `chrome/os/keyboard/layouts/gu_phone.js` |
| `keycode.js`, `parsedlayout.js`, `model.js`, `textinput.js`, `composetextinput.js`, `controller.js` | `chrome/os/keyboard/` |

`scripts/google_oracle.mjs` runs them in Node to produce the layout data and
the reference test data. `controller.js` is not run; the script copies its key
handling, and the Python port follows it.
