# DESIGN.md — Speedy direction

The design spec for this site. Everything built here derives from this file.
If code and this document disagree, one of them is wrong — fix it, don't let
them drift.

The previous direction (a dark instrument panel drawn from the optical bench)
is kept on the `instrument-panel` branch. This one takes its structure from a
reference the author chose: **speedy.io**, Awwwards Site of the Day.

---

## What this site is

A research portfolio for work on **optically pumped magnetometers (OPM)** —
atomic magnetometry, Rb vapor-cell optics, balanced polarimetry, and the
precision mechanics that hold it all still.

Two jobs, unchanged from before:

1. Read as the work of someone who builds instruments.
2. Accept new research entries later without redesign. The **양식** — the
   template and its content schema — is the deliverable; the example entries
   only prove it works.

Korean is the body language. Technical terms, part names, units and numbers
stay English.

---

## What is taken from the reference, and what is not

**Taken:** the structure and the visual grammar.

- Full-bleed sections alternating **pure black** and **pure white**, each one a
  complete surface rather than a band inside a page.
- An oversized neutral grotesque set at **line-height 1.0**, headline anchored
  to the left edge of the measure, running two or three lines.
- **Floating cards** — generously rounded, dropped over the ground with a soft
  shadow, sometimes overlapping the section edge.
- **Pill** buttons and labels, filled or outlined.
- Soft, wide **light sweeps** across the black ground, as if light were falling
  across a curved surface.
- A single sculptural object at the centre of the hero.

**Not taken:** their images, their 3D renders, their logo, their wordmark,
their copy, and their licensed Helvetica cut. None of that is ours to use, and
a portfolio wearing someone else's identity is worth less than a plain one.

Where the reference puts a rendered abstract sculpture, this site puts the
thing the work is actually about: the **FID trace**, computed from stated
parameters. Same compositional role, our own subject.

---

## Colour

The reference is monochrome, and monochrome is the right call here too — it
makes the data the only coloured thing on the page.

```
--ink            #000000   black ground
--ink-soft       #131313   raised panel on black
--ink-line       rgba(255,255,255,0.10)
--on-ink         #FFFFFF
--on-ink-dim     rgba(255,255,255,0.62)
--on-ink-faint   rgba(255,255,255,0.38)

--paper          #FFFFFF   white ground
--paper-soft     #F3F3F3   raised panel on white
--paper-line     rgba(0,0,0,0.10)
--on-paper       #000000
--on-paper-dim   rgba(0,0,0,0.58)
--on-paper-faint rgba(0,0,0,0.38)

--accent         #E63950   Rb fluorescence
--good           #17B26A
--warn           #C77700
```

The accent survives from the previous direction and keeps its job: it belongs
to the evidence chips and to nothing else. On a black-and-white page a single
red chip is unmissable, which is the point — the page should make you notice
when something is `INFERRED`.

`--good` and `--warn` are semantic only.

---

## Type

The reference sets Helvetica. That cut is licensed, so this uses a neutral
grotesque with the same skeleton from Google Fonts.

| Role | Face | Use |
|---|---|---|
| Display | **Schibsted Grotesk** 400/700 | Headlines. Line-height **1.0**, letter-spacing `-0.02em`. |
| Body | **IBM Plex Sans KR** 400/500 | Korean prose. |
| Data | **IBM Plex Mono** 400/500 | Numbers, units, labels, part names. |

```
--t-display  clamp(2.75rem, 7.5vw, 7rem)
--t-h1       clamp(2rem, 4vw, 3.5rem)
--t-h2       1.75rem
--t-h3       1.125rem
--t-body     1.0625rem
--t-small    0.9375rem
--t-label    0.75rem      mono, uppercase, tracking 0.1em
```

Display line-height is 1.0 — the reference's headlines stack tight enough that
the lines read as one block, and that is most of its character.

---

## Layout

```
--shell      1280px      content column at its widest
--gutter     clamp(1.25rem, 5vw, 4.5rem)
--measure    64ch        reading width for prose only
--radius     20px        cards
--radius-sm  8px
--pill       999px
--bar-h      72px
```

**Sections are surfaces.** Each `section` paints its own ground edge to edge
and carries its own text colours, so a black section and a white one can sit
against each other with no seam. That is the whole rhythm of the page.

**The hero** is black: light sweeps, the FID canvas as the object, the headline
over it, and two floating cards that overlap the composition — one carrying the
Larmor parameters, one carrying the standoff figure.

**The index** is white: the entry list as rows, each a card that lifts on hover.

**An entry page** alternates — black masthead with the title and metadata, then
white for the content blocks.

**Nothing centres by default.** The reference anchors its headlines to the left
of the measure and lets the right side breathe. Centre only what is genuinely
symmetrical.

---

## Motion

- Cards lift 4px and deepen their shadow on hover, over 180 ms.
- Sections reveal on scroll: 32px rise, once only, staggered 80 ms.
- The FID trace draws once on load, then idles.
- `prefers-reduced-motion: reduce` removes every transform and renders the
  trace in its final state immediately.

---

## Build rules

- No framework, no build step for the page itself. Plain HTML, CSS, ES modules.
- Fonts from Google Fonts with a real fallback stack declared.
- Images `loading="lazy"` with explicit `width`/`height`.
- Wide content scrolls inside its own container; the body never scrolls
  sideways.
- Keyboard focus always visible.
- Every colour, size and duration comes from a token. Nothing else declares one.
