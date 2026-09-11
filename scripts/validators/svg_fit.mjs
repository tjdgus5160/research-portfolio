// Every <text> in a generated figure must fit inside its own viewBox.
// A caption that runs off the right edge is silently truncated in the page.
import { chromium } from 'playwright';
import { readdirSync, readFileSync } from 'fs';
const dir = process.argv[2];
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 900, height: 600 } });
let bad = 0, n = 0;
for (const f of readdirSync(dir).filter(f => f.endsWith('.svg')).sort()) {
  const svg = readFileSync(`${dir}/${f}`, 'utf8');
  await p.setContent(`<body style="margin:0;background:#d7d7d7">${svg}</body>`);
  await p.waitForTimeout(80);
  const out = await p.evaluate(() => {
    const s = document.querySelector('svg');
    const [, , w, h] = s.getAttribute('viewBox').split(/\s+/).map(Number);
    const sc = s.getBoundingClientRect().width / w;
    const o = s.getBoundingClientRect();
    return [...s.querySelectorAll('text')].map(t => {
      const r = t.getBoundingClientRect();
      return { s: t.textContent.slice(0, 46),
               l: (r.left - o.left) / sc, r: (r.right - o.left) / sc,
               t: (r.top - o.top) / sc, b: (r.bottom - o.top) / sc, w, h };
    }).filter(x => x.l < -0.5 || x.r > x.w + 0.5 || x.t < -0.5 || x.b > x.h + 0.5);
  });
  n++;
  for (const x of out) {
    bad++;
    console.log(`  ${f}  "${x.s}"  x ${x.l.toFixed(0)}..${x.r.toFixed(0)} of ${x.w}, y ${x.t.toFixed(0)}..${x.b.toFixed(0)} of ${x.h}`);
  }
}
await b.close();
console.log(bad ? `FAIL — ${bad} label(s) outside the frame in ${n} figures` : `PASS — every label fits, ${n} figures`);
process.exit(bad ? 1 : 0);
