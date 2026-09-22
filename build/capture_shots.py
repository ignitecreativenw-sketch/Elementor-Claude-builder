#!/usr/bin/env python3
"""Re-shoot the reference with scroll-reveal animations neutralised and the
cookie banner hidden, so the full-page screenshots show real content."""
import os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reference")
URL = sys.argv[1] if len(sys.argv) > 1 else "https://REFERENCE-URL/"
SLUG = sys.argv[2] if len(sys.argv) > 2 else "home"
WIDTHS = [1440, 1024, 390]

REVEAL = r"""
() => {
  // kill cookie / consent overlays
  ['#sqs-cookie-banner-v2','.sqs-cookie-banner-v2','[id*=cookie]','[class*=cookie-banner]']
    .forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
  // neutralise scroll-reveal: only touch elements that are still hidden
  document.querySelectorAll('*').forEach(el => {
    const s = getComputedStyle(el);
    const hidden = parseFloat(s.opacity) < 0.9 || s.visibility === 'hidden'
      || (s.transform !== 'none' && /matrix\(1, 0, 0, 1, |scale|translate/.test(s.transform) === false);
    if (parseFloat(s.opacity) < 0.9) el.style.setProperty('opacity','1','important');
    if (s.visibility === 'hidden') el.style.setProperty('visibility','visible','important');
    if (el.hasAttribute('data-animation-role') || /animation|reveal|fade|slide/i.test(el.className || '')) {
      el.style.setProperty('transform','none','important');
      el.style.setProperty('opacity','1','important');
    }
  });
  document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading = 'eager');
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for w in WIDTHS:
        ctx = b.new_context(viewport={"width": w, "height": 900})
        pg = ctx.new_page()
        pg.goto(URL, wait_until="load", timeout=30000)
        pg.wait_for_timeout(2000)
        pg.evaluate("async()=>{const h=document.body.scrollHeight;for(let y=0;y<h;y+=400){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,90));}window.scrollTo(0,0);}")
        pg.wait_for_timeout(1500)
        pg.evaluate(REVEAL)
        pg.wait_for_timeout(1500)
        pg.screenshot(path=os.path.join(OUT, f"{SLUG}-{w}.png"), full_page=True)
        print("shot", w)
        ctx.close()
    b.close()
