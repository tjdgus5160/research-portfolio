# DESIGN.md — Instrument Panel

The design spec for this site. Everything built here derives from this file.
If code and this document disagree, this document is wrong or the code is —
fix one of them, don't let them drift.

---

## What this site is

A research portfolio for work on **optically pumped magnetometers (OPM)** —
atomic magnetometry, Rb vapor-cell optics, balanced polarimetry, and the
precision mechanics that hold it all still.

It has to do two things:

1. Read as the work of someone who builds instruments, not someone who
   arranged a template.
2. Accept new research entries later without redesign. The **양식** (the
   template and its content schema) is the actual deliverable; the two example
   entries only prove it works.

Korean is the body language. Technical terms, part names, units and numbers
stay English — that is how the field is written and how the author works.

---

## Where the design comes from

Not from a gallery screenshot. From the bench:

| Bench thing | Becomes |
|---|---|
| Optical breadboard, 25 mm hole pitch | The background grid, and the layout's spacing unit |
| FID — free induction decay | The hero motif: a live decaying sinusoid on Canvas |
| Rb resonance fluorescence | The accent colour |
| Anodised aluminium housing | The ground |
| Oscilloscope / instrument readouts | Monospace for every number, label and unit |
| Engineering drawing leaders and callouts | Hairlines, row rules, index numbering |

The page commits to one visual world — a dark instrument panel. That is a
choice, not an omission: there is no light theme, and every colour is painted
explicitly so the page never borrows a host background.

---

## Colour

Rubidium's D lines sit at 794.98 nm (D1) and 780.24 nm (D2) — deep red, right
at the edge of what the eye still registers. Rendered literally they are almost
black and useless as an interface colour, so the accent is the **fluorescence
as a camera records it in a dark lab**: a crimson with a rose cast, lifted
until it is legible.

The neutrals are not grey. They carry a faint red bias toward the accent, so
the ground reads as chosen rather than defaulted.

```
--ground        #0B0809   near-black anodised, faint red bias
--surface       #131011   raised panel
--surface-high  #1B1719   hover / active panel
--line          #2A2325   hairline, engraved rule
--line-bright   #3D3336   emphasised rule

--text          #EDE7E6   warm off-white
--text-dim      #9A9092   secondary
--text-faint    #6A6264   labels, units, disabled

--accent        #E63950   Rb fluorescence — the one loud colour
--accent-dim    #8E1F30   ambient glow, grid highlight, trace tail
--accent-ink    #FFF2F3   text on accent

--good          #4FB286   passes, verified
--warn          #D9A441   inferred, assumed
```

`--good` and `--warn` are semantic only. They mark evidence class on an entry,
they are never decoration, and they are not a second accent.

**Spend the boldness in one place.** The accent belongs to the FID trace, the
active index row, and the single call to action. Everywhere else is ground,
hairline and type. If something feels like it needs the accent to be legible,
the hierarchy is wrong.

---

## Type

Three roles, two families, so the page holds together.

| Role | Face | Use |
|---|---|---|
| Display | **Archivo** 700–800, tight tracking | Hero, section openers. Latin only — Korean never gets set at display weight here. |
| Body | **IBM Plex Sans KR** 400/500 | All Korean prose, entry text. |
| Data | **IBM Plex Mono** 400/500 | Numbers, units, part names, labels, index numbering, metadata. |

IBM Plex was drawn for technical documentation and it has a real Korean cut, so
Korean prose and English data sit in the same family and stop fighting.
Archivo carries the one loud typographic moment.

Scale — a fifth-based ramp, tabular figures wherever digits align:

```
--t-display   clamp(3.5rem, 11vw, 9rem)     Archivo 800, tracking -0.03em
--t-h1        clamp(2rem, 4.5vw, 3.25rem)   Archivo 700
--t-h2        1.5rem
--t-h3        1.125rem
--t-body      1.0625rem                     line-height 1.75 for Korean
--t-small     0.875rem
--t-label     0.75rem   mono, uppercase, tracking 0.14em
```

Korean needs more leading than Latin. Body copy holds ~65 characters; Korean
runs shorter per line, so the measure is set in `ch` against the body face.

---

## Layout

The 25 mm breadboard pitch is the spacing unit. Everything lands on it.

```
--u: 25px            one breadboard hole
--gutter: clamp(1.25rem, 4vw, 3rem)
--measure: 68ch
```

Three surfaces:

**1. Hero** — full viewport. The breadboard dot grid, a Canvas drawing the FID
decay, and the display type over it. Nothing else. The type says what the work
is; the trace says what it looks like.

**2. Index** — the research entries as an instrument list, not cards. One row
per entry: number, Korean title, year, method tags, arrow. Hover raises the
row, lights the rule in accent, and reveals the thumbnail. A table is the
honest form here — these are records, and records line up.

**3. Entry** — a spec sheet. A sticky left rail carries the metadata (date,
role, methods, instruments, status, evidence class). The right column carries
the content blocks. This is the part that has to survive content it has never
seen, so the block set is fixed and documented below.

---

## Content blocks

An entry is metadata plus an ordered list of blocks. These are the only block
types; adding content later means writing these, not inventing new ones.

| Block | For |
|---|---|
| `prose` | Korean body text |
| `figure` | Image + caption + evidence class |
| `data` | A table of measured or calculated values, with units |
| `equation` | A derivation step, its inputs, and what it yields |
| `spec` | Key–value parameter list, monospace, tabular |
| `code` | Commands, config, snippets |
| `note` | A callout — assumption, caveat, open question |
| `refs` | Citations that resolve to something that exists |

Every `figure` and `data` block carries an **evidence class** —
`SOURCE_FACT` / `CALCULATED` / `INFERRED` / `ILLUSTRATIVE` — rendered as a
small monospace chip. A portfolio that shows a rendering as if it were a
measurement is worth less than one that says which is which, and this project
already has the vocabulary for it.

---

## Motion

Restrained and physical. Nothing bounces.

- The FID trace draws once on load, then decays and idles. It is the page's
  one ambient moment.
- Index rows respond on hover in ~120 ms — the feel of a detent, not a slide.
- Entry content reveals on scroll, 24 px rise, staggered ~60 ms, once only.
- Everything respects `prefers-reduced-motion: reduce`: the trace renders its
  final state immediately and reveals become instant.

---

## Build rules

- No framework, no build step for the page itself. Plain HTML, CSS, ES modules.
- Fonts come from Google Fonts with a real fallback stack declared.
- Images are `loading="lazy"` with explicit `width`/`height` so nothing reflows.
- Wide content — tables, code, equations — scrolls inside its own container.
  The page body never scrolls sideways.
- Keyboard focus is always visible, and it uses the accent.
- Every interactive element is reachable and labelled.
