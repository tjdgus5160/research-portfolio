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
