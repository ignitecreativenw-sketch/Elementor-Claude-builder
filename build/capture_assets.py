#!/usr/bin/env python3
"""Pull real asset URLs (lazy logos, hero video) and the full review text."""
import json, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reference")
URL = "https://REFERENCE-URL/"

JS = r"""
() => {
  const abs = u => { try { return new URL(u, location.href).href; } catch(e){ return u; } };
  const lenders = [...document.querySelectorAll('#lenders img, [id*=lender] img')].map(i => ({
    alt: i.getAttribute('alt'),
    src: abs(i.getAttribute('data-src') || i.currentSrc || i.src).split('?')[0],
    w: Math.round(i.getBoundingClientRect().width), h: Math.round(i.getBoundingClientRect().height)
  }));
  const videos = [...document.querySelectorAll('video')].map(v => ({
    src: v.currentSrc || v.src || null,
    sources: [...v.querySelectorAll('source')].map(s => abs(s.src || s.getAttribute('src'))),
    poster: v.poster || null, loop: v.loop, muted: v.muted, autoplay: v.autoplay,
    w: v.videoWidth, h: v.videoHeight
  }));
  const bgVideoEls = [...document.querySelectorAll('[data-config-url], .sqs-video-background, [class*=video-background]')]
    .map(e => e.getAttribute('data-config-url') || e.className).slice(0,6);
  return { lenders, videos, bgVideoEls };
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    media = []
    pg.on("response", lambda r: media.append(r.url) if any(
        x in r.url for x in ('.mp4', '.webm', '.m4v')) else None)
    pg.goto(URL, wait_until="load", timeout=30000)
    pg.wait_for_timeout(3000)
    pg.evaluate("async()=>{const h=document.body.scrollHeight;for(let y=0;y<h;y+=400){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}}")
    pg.wait_for_timeout(2500)
    data = pg.evaluate(JS)
    data["videoResponses"] = sorted(set(media))

    # reviews live in a Jotform iframe
    reviews = []
    for f in pg.frames:
        try:
            r = f.evaluate(r"""() => [...document.querySelectorAll('[class*=review], [class*=card]')].map(c => c.innerText.trim()).filter(t => t.length > 40).slice(0,30)""")
            if r:
                reviews.append({"frame": f.url[:120], "items": r})
        except Exception:
            pass
    data["reviews"] = reviews
    json.dump(data, open(os.path.join(OUT, "home-assets.json"), "w"), indent=1)
    print("lenders", len(data["lenders"]), "videos", len(data["videos"]),
          "videoResponses", len(data["videoResponses"]), "reviewFrames", len(reviews))
    ctx.close(); b.close()
