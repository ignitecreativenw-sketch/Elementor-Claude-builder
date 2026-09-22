#!/usr/bin/env python3
"""Screenshot the staging build and diff it against the reference, per section."""
import json, os, sys
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
import math

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference")
QA = os.path.join(HERE, "..", "qa", "shots")
os.makedirs(QA, exist_ok=True)
TARGET = os.environ.get("STAGING_URL", "https://STAGING-URL/")
WIDTHS = [1440, 1024, 390]

SHOT_JS = r"""
() => {
  document.querySelectorAll('*').forEach(el => {
    const s = getComputedStyle(el);
    if (parseFloat(s.opacity) < 0.9) el.style.setProperty('opacity','1','important');
    if (s.visibility === 'hidden') el.style.setProperty('visibility','visible','important');
  });
  document.querySelectorAll('#wpadminbar').forEach(e => e.remove());
  document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading='eager');
}
"""

SECTIONS_JS = r"""
() => {
  const doc = document.querySelector('[data-elementor-type="wp-page"]') || document;
  return [...doc.querySelectorAll(':scope > .e-con.e-parent')].map((s,i) => {
  const r = s.getBoundingClientRect();
    return { i, top: Math.round(r.top + scrollY), h: Math.round(r.height) };
  });
}
"""


def shoot():
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in WIDTHS:
            ctx = b.new_context(viewport={"width": w, "height": 900})
            pg = ctx.new_page()
            pg.goto(TARGET, wait_until="load", timeout=40000)
            pg.wait_for_timeout(2500)
            pg.evaluate("async()=>{const h=document.body.scrollHeight;for(let y=0;y<h;y+=400){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,90));}window.scrollTo(0,0);}")
            pg.wait_for_timeout(1500)
            pg.evaluate(SHOT_JS)
            pg.wait_for_timeout(1200)
            path = os.path.join(QA, f"build-{w}.png")
            pg.screenshot(path=path, full_page=True)
            out[w] = pg.evaluate(SECTIONS_JS)
            print(f"   shot {w}: {Image.open(path).size}")
            ctx.close()
        b.close()
    json.dump(out, open(os.path.join(QA, "build-sections.json"), "w"), indent=1)
    return out


def rmse(a, b):
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    h = diff.histogram()
    total = sum(h)
    sq = sum(v * (i % 256) ** 2 for i, v in enumerate(h))
    return math.sqrt(sq / total) / 255 * 100


def compare_1440(build_sections):
    ref = Image.open(os.path.join(REF, "reference-1440.png"))
    got = Image.open(os.path.join(QA, "build-1440.png"))
    print(f"\n   reference {ref.size}   build {got.size}")
    ref_secs = json.load(open(os.path.join(REF, "home-sections.json")))["desktop"]
    # reference sections are offset by the 206px header; the build now has one too
    rows = []
    for i, bs in enumerate(build_sections):
        if i >= len(ref_secs):
            break
        rs = ref_secs[i]
        h = min(bs["h"], rs["h"], 1400)
        if h < 40:
            continue
        a = ref.crop((0, rs["top"], 1440, min(rs["top"] + h, ref.height)))
        c = got.crop((0, bs["top"], 1440, min(bs["top"] + h, got.height)))
        if a.size != c.size:
            c = c.resize(a.size)
        rows.append((i, rs["h"], bs["h"], bs["h"] - rs["h"], round(rmse(a, c), 2)))
    print(f"\n   {'S':<3}{'ref h':>8}{'build h':>9}{'delta':>8}{'RMSE %':>9}")
    for r in rows:
        print(f"   S{r[0]+1:<2}{r[1]:>8}{r[2]:>9}{r[3]:>+8}{r[4]:>9}")
    return rows


if __name__ == "__main__":
    print("==> screenshot staging")
    secs = shoot()
    print("==> diff at 1440")
    compare_1440(secs[1440])
