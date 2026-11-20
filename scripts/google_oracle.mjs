// Run Google's original ChromeOS keyboard code (third_party/google-input-tools)
// unchanged in Node, to produce:
//   - src/gujarati_phonetic/data/gu_phone.json: the layout as data for Python;
//   - tests/data/google_oracle.json.gz: what Google's engine shows and commits
//     for thousands of typed sequences, the reference the Python port must
//     match.
//
// One fix is applied to Google's layout data (not to the engine): see
// fixLayout.
//
// Usage: node scripts/google_oracle.mjs

import { readFileSync, writeFileSync } from "node:fs";
import { gzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const GOOGLE = `${ROOT}third_party/google-input-tools/`;
const ENGINE_FILES = ["keycode.js", "parsedlayout.js", "model.js", "textinput.js", "composetextinput.js"];
const BACKSPACE = "\b";

/**
 * Build a sandbox with the parts of the Closure library the engine uses.
 * @returns {object} The sandbox, with `commits` and `loaded` filled by the engine.
 */
function makeSandbox() {
  const sandbox = { commits: [], loaded: [] };
  const provide = (name) => {
    let node = sandbox;
    for (const part of name.split(".")) {
      node[part] ??= {};
      node = node[part];
    }
  };
  function EventTarget() {}
  EventTarget.prototype.dispatchEvent = () => true;
  sandbox.goog = {
    provide,
    require: () => {},
    inherits: (child, parent) => {
      child.prototype = Object.create(parent.prototype);
      child.prototype.constructor = child;
      child.superClass_ = parent.prototype;
    },
    base: (me, ...args) => Object.getPrototypeOf(Object.getPrototypeOf(me)).constructor.apply(me, args),
    bind: (fn, self) => fn.bind(self),
    exportSymbol: (name, value) => {
      sandbox[name] = value;
    },
    abstractMethod: () => {
      throw new Error("abstract");
    },
    nullFunction: () => {},
    object: {
      clone: (obj) => ({ ...obj }),
      create: (pairs) => {
        const obj = {};
        for (let i = 0; i < pairs.length; i += 2) obj[pairs[i]] = pairs[i + 1];
        return obj;
      },
    },
    string: { endsWith: (text, suffix) => text.endsWith(suffix) },
    events: { EventTarget },
    net: { jsloader: {} },
  };
  provide("i18n.input.chrome.vk");
  const vk = sandbox.i18n.input.chrome.vk;
  vk.EventType = { LAYOUT_LOADED: "ll" };
  vk.LayoutEvent = function LayoutEvent(type, layoutView) {
    this.type = type;
    this.layoutView = layoutView;
  };
  vk.DeferredApi = {
    setComposition: () => {},
    commitText: (contextId, text) => sandbox.commits.push(text),
  };
  return sandbox;
}

/**
 * Fix the consonant + y rules of gu_phone.js.
 *
 * In Google's file the plain rules (consonant + "y" gives the "ya" conjunct)
 * are commented out, and the nukta rules that follow them were written with a
 * lowercase "y" instead of "Y", the key of every other nukta letter (R, q, G,
 * z, J, f, Y). As is, vidyArthI gives "વિદ્ય઼આર્થી" and "વિદ્યાર્થી" cannot be
 * typed. Each such rule becomes two: "Y" with the nukta, as written, and "y"
 * without it, as in the commented-out lines.
 * @param {object} layout The raw layout.
 * @returns {object} The layout with the fixed rules, in the same order.
 */
function fixLayout(layout) {
  const NUKTA_YA = "\u0AAF\u0ABC";
  const transform = {};
  for (const [pattern, replacement] of Object.entries(layout.transform)) {
    if (pattern.endsWith("y") && replacement.endsWith(NUKTA_YA)) {
      transform[`${pattern.slice(0, -1)}Y`] = replacement;
      transform[pattern] = replacement.slice(0, -1);
    } else {
      transform[pattern] = replacement;
    }
  }
  return { ...layout, transform };
}

/**
 * Load the engine and the Gujarati phonetic layout.
 * @returns {{sandbox: object, layout: object}} The loaded engine and the raw layout.
 */
function loadEngine() {
  const sandbox = makeSandbox();
  vm.createContext(sandbox);
  for (const file of ENGINE_FILES) {
    vm.runInContext(readFileSync(GOOGLE + file, "utf8"), sandbox, { filename: file });
  }
  vm.runInContext("var model = new i18n.input.chrome.vk.Model();", sandbox);
  // Keep the raw layout object before the engine parses it.
  const engineLoadme = sandbox.cros_vk_loadme;
  sandbox.cros_vk_loadme = (layout) => {
    const fixed = fixLayout(layout);
    sandbox.loaded.push(fixed);
    engineLoadme(fixed);
  };
  vm.runInContext(readFileSync(`${GOOGLE}gu_phone.js`, "utf8"), sandbox, { filename: "gu_phone.js" });
  return { sandbox, layout: sandbox.loaded[0] };
}

/**
 * Type one sequence into the engine, from an empty history, as the ChromeOS
 * controller does.
 * @param {object} sandbox The loaded engine.
 * @param {string} keys The typed characters; "\b" is Backspace.
 * @returns {Array<[boolean, string, string]>} Per key: handled, text
 *     committed by this key, composition shown after it. A final entry with
 *     key "reset" commits what is left.
 */
function typeSequence(sandbox, keys) {
  const vk = sandbox.i18n.input.chrome.vk;
  const model = sandbox.model;
  model.activateLayout("gu_phone");
  model.clearHistory();
  const parsed = model.layouts_["gu_phone"];
  const input = new vk.ComposeTextInput({ contextID: 1 }, model);
  // Characters a US keyboard sends, from the layout's own key tables.
  const typeable = new Set();
  for (const state of ["", "s", "l", "sl"]) {
    for (const item of Object.values(parsed.view.mappings[state])) typeable.add(item[2]);
  }
  const steps = [];
  for (const key of keys) {
    sandbox.commits.length = 0;
    // Controller.commitChars_: the key's chars, Space as a space, others none.
    let chars = key !== BACKSPACE && typeable.has(key) ? key : null;
    if (!chars && key === " ") chars = " ";
    let handled = false;
    if (chars !== null || key === BACKSPACE) {
      let trans = { back: 1, chars: "" };
      const text = input.textBeforeCursor;
      if (key === BACKSPACE) {
        model.processBackspace(text);
      } else {
        trans = model.translate(chars, text);
      }
      handled = input.commitText(trans.chars, trans.back);
    }
    steps.push([handled, sandbox.commits.join(""), input.textBeforeCursor]);
  }
  sandbox.commits.length = 0;
  input.reset();
  steps.push([true, sandbox.commits.join(""), input.textBeforeCursor]);
  return steps;
}

/**
 * Deterministic pseudo-random numbers (mulberry32).
 * @param {number} seed The seed.
 * @returns {function(): number} A generator of numbers in [0, 1).
 */
function random(seed) {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// The sequences: every single key and pair, triples of the phonetic keys,
// common words, and random runs with spaces and Backspace.
const PRINTABLE = Array.from({ length: 95 }, (_, i) => String.fromCharCode(32 + i));
const PHONETIC = [..."aAiIuUeEoOkKgGcCjJTDNtdnpbmyrlLvwSshRqzfYxMH.~^"];
const WORDS = [
  "kem Cho", "namaste", "gujarAtI", "aapaNe", "kRShNa", "shrI", "OM", "praShna", "vidyArthI",
  "mahArAShTra", "bhAShA", "dhanyavAd", "kShamA", "j~nAna", "patra", "sarkAr", "adAlat", "nyAy",
  "amadAvAd", "rAjkoT", "suprabhAt", "kAryAlay", "taiyAr", "auShadh", "R^iShi", "kR^iShNa",
  "sha.nkar", "ha.Ns", "a.ngrejI", "ka.ch", "Thak", "Dhol", "ghar", "jhaghaDo", "chaa", "Chokaro",
];
const sequences = [];
for (const a of PRINTABLE) sequences.push(a);
for (const a of PHONETIC) for (const b of PHONETIC) sequences.push(a + b);
for (const a of PHONETIC) for (const b of PHONETIC) for (const c of "aAiIuUeoh.~^kty ") sequences.push(a + b + c);
for (const word of WORDS) {
  sequences.push(word, `${word} `, `${word}\b`, `${word}\b\b`);
}
const next = random(20261120);
const pool = [...PHONETIC, " ", " ", BACKSPACE, ",", "1", "-"];
for (let n = 0; n < 4000; n++) {
  const length = 1 + Math.floor(next() * 14);
  sequences.push(Array.from({ length }, () => pool[Math.floor(next() * pool.length)]).join(""));
}

const { sandbox, layout } = loadEngine();
const data = {
  id: layout.id,
  title: layout.title,
  mappings: layout.mappings,
  transforms: Object.entries(layout.transform),
  history_prune_regex: layout.historyPruneRegex,
};
writeFileSync(`${ROOT}src/gujarati_phonetic/data/gu_phone.json`, `${JSON.stringify(data, null, 1)}\n`);

const cases = sequences.map((keys) => ({ keys, steps: typeSequence(sandbox, keys) }));
writeFileSync(`${ROOT}tests/data/google_oracle.json.gz`, gzipSync(`${JSON.stringify(cases)}\n`, { level: 9 }));
console.log(`${data.transforms.length} rules, ${cases.length} sequences`);
