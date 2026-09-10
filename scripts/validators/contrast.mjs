/* Measure contrast the way a reader meets it: computed styles, in a browser,
 * on the real pages, in both palettes.
 *
 * The first version of this gate inferred each element's background from its
 * selector with regexes. It produced false positives (.skip declares its own
 * background), false negatives (.ticker-run inherits from .ticker) and was
 * defeated twice by substring matching — ".bar-nav a:not(.btn)" contains
 * ".btn". Guessing was the wrong tool. This reads what the browser actually
 * paints, so there is nothing left to guess.
 *
 *   node scripts/validators/contrast.mjs [baseUrl]
 */
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const ROOT = new URL('../..', import.meta.url).pathname;
// listed by hand once and then forgotten, which is how the theory page went
// unchecked; derived from the directory instead
const PAGES = ['/index.html', '/en/index.html', '/gallery.html',
               ...(await import('node:fs')).readdirSync(
                     new URL('../../work', import.meta.url).pathname)
                  .filter(f => f.endsWith('.html')).map(f => '/work/' + f),
               '/work/w01-rb-cell-optics.html',
               '/work/w02-balanced-polarimeter.html',
               '/work/w03-supervised-pipeline.html']
  .filter((v, i, a) => a.indexOf(v) === i);
const TYPES = { '.html': 'text/html; charset=utf-8', '.css': 'text/css',
                '.js': 'text/javascript', '.mjs': 'text/javascript',
                '.png': 'image/png', '.jpg': 'image/jpeg', '.json': 'application/json',
                '.svg': 'image/svg+xml' };

const serve = () => new Promise((res) => {
  const s = createServer(async (req, rep) => {
    const p = join(ROOT, normalize(decodeURI(req.url.split('?')[0])));
    try {
      if ((await stat(p)).isDirectory()) throw 0;
      rep.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream',
                           'cache-control': 'no-store' });
      rep.end(await readFile(p));
    } catch { rep.writeHead(404); rep.end('no'); }
  });
  s.listen(0, '127.0.0.1', () => res([s, `http://127.0.0.1:${s.address().port}`]));
});

const AUDIT = () => {
  const parse = (c) => (c.match(/[\d.]+/g) || []).map(Number);
  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const lum = ([r, g, b]) => 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
  const over = (fg, bg) => fg.length < 4 || fg[3] === 1 ? fg.slice(0, 3)
    : fg.slice(0, 3).map((c, i) => c * fg[3] + bg[i] * (1 - fg[3]));

  // the first ancestor that actually paints, composited down to the page
  const ground = (el) => {
    let stack = [];
    for (let n = el; n; n = n.parentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c.length && (c.length < 4 || c[3] > 0)) stack.push(c);
      if (c.length >= 3 && (c.length < 4 || c[3] === 1)) break;
    }
    let out = [255, 255, 255];
    for (const c of stack.reverse()) out = over(c, out);
    return out;
  };

  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    if (el.closest('[aria-hidden="true"]')) continue;          // decoration
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const bg = ground(el);
    const fg = over(parse(cs.color), bg);
    const L = [lum(fg), lum(bg)].sort((a, b) => b - a);
    const ratio = (L[0] + 0.05) / (L[1] + 0.05);
    const size = parseFloat(cs.fontSize);
    const bold = +cs.fontWeight >= 700;
    const need = (size >= 24 || (size >= 18.66 && bold)) ? 3 : 4.5;
    if (ratio < need) {
      out.push({ tag: el.tagName.toLowerCase(),
                 cls: (el.className || '').toString().split(' ')[0],
                 text: el.textContent.trim().slice(0, 28),
                 ratio: +ratio.toFixed(2), need, size });
    }
  }
  return out;
};

const [server, base] = await serve();
const browser = await chromium.launch();
let failures = 0, checked = 0;
for (const pal of ['mono', 'dmg']) {
  for (const path of PAGES) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.goto(base + path, { waitUntil: 'load' });
    await page.evaluate((p) => {
      document.getElementById('boot')?.remove();
      document.documentElement.classList.remove('booting');
      document.documentElement.dataset.pal = p;
      document.querySelectorAll('[data-r]').forEach((e) => e.classList.add('r1', 'r2', 'r3'));
    }, pal);
    await page.waitForTimeout(220);
    const bad = await page.evaluate(AUDIT);
    checked += await page.evaluate(() => document.querySelectorAll('body *').length);
    for (const b of bad) {
      failures++;
      console.log(`  FAIL  ${pal} ${path}  <${b.tag}.${b.cls}> ${b.ratio}:1 ` +
                  `(need ${b.need} at ${b.size}px)  "${b.text}"`);
    }
    await page.close();
  }
}
await browser.close();
server.close();
console.log();
console.log(failures
  ? `FAIL — ${failures} element(s) below AA across ${PAGES.length} pages x 2 palettes`
  : `PASS — every rendered text element clears AA, ${checked} elements walked`);
process.exit(failures ? 1 : 0);
