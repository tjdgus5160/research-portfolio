// Typeset every equation in content/entries/*.json, once, at build time.
//
// KaTeX is asked for MathML only. The HTML output would need katex.css and a
// dozen webfonts; the MathML is self-contained, inherits the page's colour and
// palette like any other element, needs no script at run time, and is what a
// screen reader wants anyway. The <annotation> KaTeX includes carries the
// original LaTeX, so the source survives copy-paste.
//
//   node scripts/render_math.mjs [--check]
//
// Writes content/math.json, a {tex: mathml} cache the Python build reads. The
// cache is committed so the site can be built without node, and --check fails
// if an equation has been edited without re-rendering.
import katex from 'katex';
import { readFileSync, writeFileSync, readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'content', 'math.json');
const check = process.argv.includes('--check');

const tex = [];
const seen = new Set();
const dir = join(ROOT, 'content', 'entries');
for (const f of readdirSync(dir).filter(f => f.endsWith('.json')).sort()) {
  const e = JSON.parse(readFileSync(join(dir, f), 'utf8'));
  for (const eq of (e.geometry?.equations ?? [])) {
    if (eq.tex && !seen.has(eq.tex)) { seen.add(eq.tex); tex.push(eq.tex); }
  }
}

const out = {};
let bad = 0;
for (const t of tex) {
  try {
    // displayMode centres and gives operators room; strict rejects the silent
    // fallbacks KaTeX would otherwise make for a typo.
    out[t] = katex.renderToString(t, {
      output: 'mathml', displayMode: true, throwOnError: true, strict: 'error',
    }).replace(/^<span class="katex">/, '').replace(/<\/span>$/, '');
  } catch (err) {
    bad++;
    console.log(`  FAIL  ${t}\n        ${err.message.split('\n')[0]}`);
  }
}
if (bad) { console.log(`\nFAIL — ${bad} of ${tex.length} did not typeset`); process.exit(1); }

const body = JSON.stringify(out, Object.keys(out).sort(), 2) + '\n';
if (check) {
  let cur = '';
  try { cur = readFileSync(OUT, 'utf8'); } catch {}
  if (cur === body) { console.log(`  up to date — ${tex.length} equations`); process.exit(0); }
  console.log('  WOULD CHANGE — run: node scripts/render_math.mjs');
  process.exit(1);
}
writeFileSync(OUT, body);
console.log(`  typeset ${tex.length} equations -> content/math.json`);
