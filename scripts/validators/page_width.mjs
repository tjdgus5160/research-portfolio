// No page may scroll sideways, at any width this design claims to support.
//
// Added after typeset equations shipped with the classic grid bug: a grid item
// defaults to min-width:auto, so the track grew to the widest formula and the
// overflow-x:auto on the inner box never engaged. The page reported a 525px
// scroll width in a 390px viewport and clipped the right edge of every wide
// equation, unreachably. Eyeballing found it once; this finds it every time.
//
//   node scripts/validators/page_width.mjs [--base http://127.0.0.1:8788]
import { chromium } from 'playwright';
import { readdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const i = process.argv.indexOf('--base');
const BASE = i > -1 ? process.argv[i + 1] : 'http://127.0.0.1:8788';
const WIDTHS = [360, 390, 768, 1024, 1440];

const pages = ['index.html', 'en/index.html',
  ...readdirSync(join(ROOT, 'work')).filter(f => f.endsWith('.html')).sort()
      .map(f => `work/${f}`)];

const b = await chromium.launch();
const page = await b.newPage();
let bad = 0, n = 0;
for (const w of WIDTHS) {
  await page.setViewportSize({ width: w, height: 900 });
  for (const u of pages) {
    await page.goto(`${BASE}/${u}`, { waitUntil: 'load' });
    await page.waitForTimeout(120);
    n++;
    const r = await page.evaluate(() => {
      const d = document.scrollingElement;
      if (d.scrollWidth <= d.clientWidth + 1) return null;
      // name the widest thing that is not inside something that scrolls
      const W = d.clientWidth;
      const scrolls = el => {
        for (let a = el.parentElement; a; a = a.parentElement) {
          const o = getComputedStyle(a).overflowX;
          if (o === 'auto' || o === 'scroll' || o === 'hidden') return true;
        }
        return false;
      };
      let worst = null;
      for (const el of document.querySelectorAll('body *')) {
        const b = el.getBoundingClientRect();
        if (b.right > W + 1 && b.width > 0 && !scrolls(el)
            && (!worst || b.right > worst.right))
          worst = { right: Math.round(b.right), tag: el.tagName,
                    cls: (el.className.baseVal ?? el.className ?? '').toString().slice(0, 40) };
      }
      return { scrollW: d.scrollWidth, clientW: W, worst };
    });
    if (r) {
      bad++;
      const w2 = r.worst ? `${r.worst.tag}.${r.worst.cls} to ${r.worst.right}px` : 'no single culprit';
      console.log(`  FAIL  ${u} at ${w}px — scrollWidth ${r.scrollW} > ${r.clientW}  (${w2})`);
    }
  }
}
await b.close();
console.log();
console.log(bad ? `FAIL — ${bad} of ${n} page/width combinations scroll sideways`
                : `PASS — no sideways scroll, ${pages.length} pages x ${WIDTHS.length} widths`);
process.exit(bad ? 1 : 0);
