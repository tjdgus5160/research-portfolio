# AGENTS.md — rules for working in this repository

**This is the single source of project rules.** Every agent reads this first.
If another document contradicts it, this file wins. `DESIGN.md` is the design
spec and is binding in the same way for anything visual.

---

## 1. What this is

A research portfolio site for work on **optically pumped magnetometers**.

The deliverable is the **양식** — the template and its content schema. Research
entries get written into it later. Build it so that adding an entry means
writing content, never redesigning.

Body language is Korean. Technical terms, part names, units and numbers stay
English.

---

## 2. Roles

| | Claude Code | OpenCode / Qwen |
|---|---|---|
| Role | design lead, supervisor | builder |
| Owns | `DESIGN.md`, `assets/css/tokens.css`, `assets/js/fid.js` | components, templates, content loader |
| Judges | PASS/FAIL on every gate | — |

**Do not edit `DESIGN.md`, `tokens.css` or `fid.js`.** They carry the design
decisions. If one of them blocks you, say so and stop — do not work around it.

---

## 3. The rule that matters most

**Never declare a raw value.** Every colour, size, font, duration and easing
comes from a token in `tokens.css`. A hex code, a `px` font-size or a bare
`ms` anywhere else is a bug, and the gate fails the task for it.

If a value you need has no token, that is a design decision and it is not
yours to make. Report it.

---

## 4. Content and honesty

Entries carry an **evidence class** on every figure and data block:

| Class | Means |
|---|---|
| `SOURCE_FACT` | Stated in a cited source |
| `CALCULATED` | Derived — record the equation and inputs |
| `INFERRED` | A reasoned assumption — record the reasoning |
| `ILLUSTRATIVE` | Present so the picture reads. No physical claim. |

A rendering shown as if it were a measurement is a defect, not a style choice.
Placeholder content in the example entries must be obviously placeholder —
never a plausible-looking fake measurement.

**Never invent a citation.**

---

## 5. Build rules

- No framework and no build step for the page. Plain HTML, CSS, ES modules.
- Fonts from Google Fonts, with a real fallback stack declared.
- Images: `loading="lazy"` plus explicit `width`/`height`.
- Wide content (tables, code, equations) scrolls inside its own
  `overflow-x: auto` container. The page body never scrolls sideways.
- Keyboard focus is always visible and uses `--focus`.
- Everything interactive is reachable by keyboard and labelled.
- Respect `prefers-reduced-motion: reduce`.
- Semantic HTML. One `<h1>` per page, headings in order, landmarks present.

## 7. How to get work out of the local model

Measured on this machine, and both parts are needed:

**`reasoning_effort: "minimal"`** is set in `opencode.json`. Without it the model
spends its whole budget thinking and emits no code at all — 11,317 characters of
reasoning and zero CSS, one observed thought lasting 29 minutes 54 seconds
before the request timed out. With it, thoughts run about 2.7 seconds.

**Prompts must be self-contained.** At ~17 tok/s every tool round-trip is
expensive, and a brief that says "read these five files first" burns the turn on
exploration and ends without writing anything. Put the token list, the class
list and the constraints directly in the prompt, say "do not read any files
first", and ask for exactly one file per call.

A dispatch that follows both wrote a clean 90-line stylesheet in 161 seconds.

---

## 6. Working under orchestration

Do the dispatched task, nothing else. Blocked? `orca orchestration ask`.
Report once with `worker_done`, and `--outcome failed` when it failed —
a failure stated plainly is worth more than a success claimed loosely.

Write **one file per tool call**. The local model's stream will not survive a
single large write; a modest file per call survives interruption.
