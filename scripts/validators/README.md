# Gates

## Superseded: `validate_structure.py`

It existed to prove one thing — that the adopted design had not been altered —
by comparing `index.html`'s tag/class/id skeleton against a pinned commit and
byte-comparing `styles.css` and `script.js`. It did that job for the whole life
of the webisoft-derived build and caught two real regressions: a worker that
reported PASS on a section it never wrote, and a brief of mine that dropped two
nodes by specifying `서울, 대한민국` without its `<br />`.

**It no longer describes what this project wants to be true.** The author has
commissioned a full redesign — an original 8-bit, four-tone handheld interface —
so `index.html`, `styles.css` and `script.js` are all deliberately new. Running
this gate now reports a failure that is the intended outcome, which makes it
worse than no gate: a check you are expected to override teaches you to override
checks.

The file is left in place rather than deleted, and rather than re-baselined onto
the new design, because neither is mine to decide:

- **Delete it** if the design is now expected to keep moving.
- **Re-baseline it** (point `structure-base.txt` at the 8-bit commit, empty
  `structure-allow.txt`) if the new design should be locked the way the old one
  was.

Until one of those is chosen, do not run it and do not treat its failure as a
regression. The previous design is fully recoverable from git history, and the
cinematic-hero work that was in the tree before the rewrite is preserved in
`git stash` — see `git stash list`.

## Live: `validate_copy.py`

This one still earns its place, and matters *more* after a redesign than before:
it proves the research content survived the visual rewrite. It checks that every
required per-section string is present and that no copy from the original
template remains.

    python3 scripts/validators/validate_copy.py

Its `CREDIT` rule was written for the webisoft attribution line and has been
updated — the new interface is original, so there is no longer a design to
attribute.

## Live: `build_gallery.py --check`

Reports whether the generated-image log has drifted from what ComfyUI has
produced. Not a gate, but it fails loudly when the page is stale.

    python3 scripts/build_gallery.py --check

## Live: `validate_math.py`

Every equation on the site names a source id from `content/sources.json`. This
proves each one resolves, that the typeset cache is current, and that a source
claiming to be on disk is still there with the sha256 it claims.

    python3 scripts/validators/validate_math.py

It also enforces the rule that matters: a source marked `named` — cited by
something held here, but not held itself — can never back a `SOURCE_FACT`.

## Live: `page_width.mjs`

No page may scroll sideways at 360, 390, 768, 1024 or 1440px. Needs a server:

    python3 -m http.server 8788 &
    node scripts/validators/page_width.mjs

Written after typeset equations shipped with a grid `min-width:auto` bug that
clipped the right edge of every wide formula on a phone, unreachably. It names
the widest element that is not inside a scroll container, so the failure points
at its own cause.

## Live: `svg_fit.mjs`

Every `<text>` in a generated figure must fall inside its own viewBox. Catches
captions that run off the right edge, which are silently cropped on the page.

    node scripts/validators/svg_fit.mjs assets/diagrams

## Typesetting

`node scripts/render_math.mjs` renders every equation to MathML through KaTeX
and writes `content/math.json`. MathML rather than KaTeX's HTML: no stylesheet,
no webfonts, it inherits `--t0..--t3` so it follows the palette switch, and it
survives with scripting off. The cache is committed so the site builds without
node; `--check` fails if an equation was edited without re-rendering.

## Superseded: `validate_site.py`

**Do not run it. Every failure it reports is false.**

It checks a directory layout this site no longer has: it globs
`assets/css/*.css`, `assets/js/*.js` and expects `assets/css/tokens.css`. The
CSS and JS live at the repository root (`styles.css`, `entry.css`, `script.js`),
so those globs match nothing and the checks fail vacuously. Three of them are
accessibility checks, and all three features are in fact implemented — verified
in a browser on 2026-09-13:

| what it reports missing | what is actually there |
|---|---|
| a visible focus state | `:focus-visible` in `styles.css`, measured as a 4px solid outline |
| reduced motion honoured | `script.js` reads the media query; zero elements animate under `reducedMotion: reduce` |
| wide content scroll container | `overflow-x: auto` on `.e-scroll` and `.eq-math`, measured as computed style |

It also audits `v2.html`, `v3.html` and `awwwards-study.html`, which are
untracked files left in the working tree by another agent and are not part of
the site.

What replaced it, by concern: `contrast.mjs` for colour and `page_width.mjs` for
scroll containers — both of which measure the rendered page instead of grepping
source — and `validate_copy.py` for content.

## Superseded: `validate_content.py`

Looks for `content/entries/01-rb-cell-optics.json` and
`02-balanced-polarimeter.json`. Those were renamed to `w01-` and `w02-` when the
theory entries arrived and needed a prefix of their own, so it fails on two
files that have not existed under those names for some time.

Replaced by `validate_math.py` (sources, citations, artifact paths),
`build_entries.py --check` (the pages match their JSON) and `validate_copy.py`
(the required copy is present).

---

Both are left in place rather than deleted, for the same reason
`validate_structure.py` is: re-baselining or deleting a gate is the author's
call, not the supervisor's. But note the asymmetry — `validate_structure.py`
fails because the design deliberately changed, whereas these two fail because
they are looking in the wrong place. A check that cannot pass teaches you to
ignore checks.
