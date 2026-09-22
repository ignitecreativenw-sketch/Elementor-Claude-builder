#!/usr/bin/env python3
"""Capture a reference site as text-first artefacts for the Elementor clone build.

Outputs (into ../reference relative to this file):
  screenshot-<w>.png        full-page at 1440 / 1024 / 390
  design-tokens.json        per-breakpoint computed-style tokens
  content.json              sections in DOM order with text/buttons/images
  combined.css              all stylesheet text (reference only)
"""
import json, os, sys, re
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "reference")
os.makedirs(OUT, exist_ok=True)

URL = sys.argv[1] if len(sys.argv) > 1 else "https://REFERENCE-URL/"
SLUG = sys.argv[2] if len(sys.argv) > 2 else "home"
WIDTHS = [(1440, "desktop"), (1024, "tablet"), (390, "mobile")]

TOKENS_JS = r"""
() => {
  const cs = el => getComputedStyle(el);
  const px = v => v;
  const seenColors = {};
  const addColor = (c) => {
    if (!c) return;
    if (c === 'rgba(0, 0, 0, 0)' || c === 'transparent') return;
    seenColors[c] = (seenColors[c] || 0) + 1;
  };
  const fonts = {};
  document.querySelectorAll('body *').forEach(el => {
    const s = cs(el);
    if (el.offsetParent === null && s.position !== 'fixed') return;
    addColor(s.color); addColor(s.backgroundColor);
    if (s.borderTopWidth !== '0px') addColor(s.borderTopColor);
    const key = s.fontFamily.split(',')[0].replace(/["']/g,'').trim() + '|' + s.fontWeight;
    fonts[key] = (fonts[key] || 0) + 1;
  });

  const typo = {};
  ['h1','h2','h3','h4','h5','h6','p','li','a','button'].forEach(tag => {
    const els = [...document.querySelectorAll(tag)].filter(e => e.offsetParent !== null && e.textContent.trim());
    if (!els.length) return;
    const variants = {};
    els.slice(0, 40).forEach(e => {
      const s = cs(e);
      const k = JSON.stringify({
        family: s.fontFamily.split(',')[0].replace(/["']/g,'').trim(),
        size: s.fontSize, weight: s.fontWeight, lineHeight: s.lineHeight,
        letterSpacing: s.letterSpacing, color: s.color,
        transform: s.textTransform, align: s.textAlign
      });
      variants[k] = (variants[k] || 0) + 1;
    });
    typo[tag] = Object.entries(variants).sort((a,b)=>b[1]-a[1]).slice(0,4)
      .map(([k,n]) => ({...JSON.parse(k), count: n}));
  });

  // Buttons / links styled as buttons
  const btns = [...document.querySelectorAll('a,button')].filter(e => {
    if (e.offsetParent === null) return false;
    const s = cs(e);
    return (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent')
        || parseFloat(s.borderTopWidth) > 0;
  }).slice(0, 12).map(e => {
    const s = cs(e);
    return { text: e.textContent.trim().slice(0,40), bg: s.backgroundColor, color: s.color,
      padding: s.padding, radius: s.borderRadius, border: s.border, fontSize: s.fontSize,
      fontWeight: s.fontWeight, letterSpacing: s.letterSpacing, textTransform: s.textTransform,
      width: Math.round(e.getBoundingClientRect().width),
      height: Math.round(e.getBoundingClientRect().height) };
  });

  // Top-level sections
  const roots = [...document.querySelectorAll('body > *, main > *, body > div > section, body > div > div')]
    .filter(e => e.getBoundingClientRect().height > 60);
  const sections = [];
  const pick = [];
  const main = document.querySelector('main') || document.body;
  [...main.children].forEach(e => { if (e.getBoundingClientRect().height > 40) pick.push(e); });
  const flat = pick.length > 2 ? pick : roots;
  flat.slice(0, 40).forEach((el, i) => {
    const s = cs(el);
    const r = el.getBoundingClientRect();
    const inner = [...el.querySelectorAll('*')].find(c => {
      const w = c.getBoundingClientRect().width;
      return w > 0 && w < r.width - 20 && cs(c).marginLeft === cs(c).marginRight && w > 300;
    });
    sections.push({
      index: i, tag: el.tagName.toLowerCase(),
      id: el.id || null, cls: (el.className || '').toString().slice(0, 140),
      height: Math.round(r.height), width: Math.round(r.width),
      display: s.display, flexDirection: s.flexDirection, flexWrap: s.flexWrap,
      justifyContent: s.justifyContent, alignItems: s.alignItems, gap: s.gap,
      padding: s.padding, margin: s.margin,
      background: s.backgroundColor,
      backgroundImage: s.backgroundImage === 'none' ? null : s.backgroundImage.slice(0, 200),
      textAlign: s.textAlign,
      innerMaxWidth: inner ? Math.round(inner.getBoundingClientRect().width) : null
    });
  });

  return {
    viewport: { width: window.innerWidth, height: window.innerHeight },
    documentHeight: Math.round(document.documentElement.scrollHeight),
    colors: Object.entries(seenColors).sort((a,b)=>b[1]-a[1]).slice(0,24).map(([c,n])=>({color:c,count:n})),
    fonts: Object.entries(fonts).sort((a,b)=>b[1]-a[1]).slice(0,16).map(([f,n])=>({font:f,count:n})),
    typography: typo,
    buttons: btns,
    sections: sections
  };
}
"""

CONTENT_JS = r"""
() => {
  const main = document.querySelector('main') || document.body;
  const kids = [...main.children].filter(e => e.getBoundingClientRect().height > 40);
  const roots = kids.length > 2 ? kids : [...document.querySelectorAll('body > *')].filter(e => e.getBoundingClientRect().height > 60);
  const abs = u => { try { return new URL(u, location.href).href; } catch(e){ return u; } };
  return roots.slice(0, 40).map((el, i) => {
    const r = el.getBoundingClientRect();
    const headings = [...el.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({
      level: h.tagName.toLowerCase(), text: h.innerText.trim() }));
    const paras = [...el.querySelectorAll('p')].map(p => p.innerText.trim()).filter(Boolean);
    const buttons = [...el.querySelectorAll('a,button')].map(a => ({
      text: (a.innerText||'').trim(), href: a.getAttribute('href') ? abs(a.getAttribute('href')) : null
    })).filter(b => b.text);
    const images = [...el.querySelectorAll('img')].map(im => {
      const ir = im.getBoundingClientRect();
      return { src: abs(im.currentSrc || im.src), alt: im.getAttribute('alt'),
        rendered: [Math.round(ir.width), Math.round(ir.height)],
        natural: [im.naturalWidth, im.naturalHeight] };
    });
    const bgEls = [...el.querySelectorAll('*')].map(e => getComputedStyle(e).backgroundImage)
      .filter(b => b && b !== 'none' && b.includes('url(')).slice(0,6);
    const lists = [...el.querySelectorAll('ul,ol')].slice(0,8).map(u =>
      [...u.querySelectorAll('li')].map(li => li.innerText.trim()).filter(Boolean));
    const fields = [...el.querySelectorAll('input,textarea,select')].map(f => ({
      type: f.type || f.tagName.toLowerCase(), name: f.name || null,
      placeholder: f.getAttribute('placeholder') || null, required: f.required }));
    const svgs = el.querySelectorAll('svg').length;
    return { index: i, tag: el.tagName.toLowerCase(), id: el.id || null,
      cls: (el.className||'').toString().slice(0,140),
      top: Math.round(r.top + scrollY), height: Math.round(r.height),
      headings, paragraphs: paras, buttons, images, backgroundImages: bgEls,
      lists, formFields: fields, svgCount: svgs,
      text: el.innerText.trim().slice(0, 1200) };
  });
}
"""

HEAD_JS = r"""
() => ({
  title: document.title,
  metaDescription: (document.querySelector('meta[name=description]')||{}).content || null,
  canonical: (document.querySelector('link[rel=canonical]')||{}).href || null,
  og: [...document.querySelectorAll('meta[property^="og:"]')].map(m=>({p:m.getAttribute('property'),c:m.content})),
  h1Count: document.querySelectorAll('h1').length,
  nav: [...document.querySelectorAll('header a, nav a')].map(a=>({text:a.innerText.trim(), href:a.href})).filter(a=>a.text).slice(0,40),
  footerLinks: [...document.querySelectorAll('footer a')].map(a=>({text:a.innerText.trim(), href:a.href})).filter(a=>a.text).slice(0,40),
  generator: (document.querySelector('meta[name=generator]')||{}).content || null,
  scripts: [...document.querySelectorAll('script[src]')].map(s=>s.src).slice(0,60),
  stylesheets: [...document.querySelectorAll('link[rel=stylesheet]')].map(s=>s.href).slice(0,40)
})
"""

def main():
    tokens = {}
    content = None
    head = None
    css_text = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for w, label in WIDTHS:
            ctx = browser.new_context(viewport={"width": w, "height": 900},
                                      device_scale_factor=1,
                                      user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"))
            page = ctx.new_page()
            page.goto(URL, wait_until="load", timeout=30000)
            page.wait_for_timeout(2500)
            # trigger lazy loads
            page.evaluate("async()=>{const h=document.body.scrollHeight;for(let y=0;y<h;y+=600){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,120));}window.scrollTo(0,0);}")
            page.wait_for_timeout(1200)
            page.screenshot(path=os.path.join(OUT, f"{SLUG}-{w}.png"), full_page=True)
            tokens[label] = page.evaluate(TOKENS_JS)
            if label == "desktop":
                content = page.evaluate(CONTENT_JS)
                head = page.evaluate(HEAD_JS)
                for link in head["stylesheets"]:
                    try:
                        r = page.request.get(link, timeout=15000)
                        if r.ok:
                            css_text.append(f"/* ==== {link} ==== */\n" + r.text())
                    except Exception as e:
                        css_text.append(f"/* failed {link}: {e} */")
            else:
                tokens[label]["content"] = page.evaluate(CONTENT_JS)
            ctx.close()
        browser.close()

    json.dump(tokens, open(os.path.join(OUT, f"{SLUG}-design-tokens.json"), "w"), indent=1)
    json.dump({"url": URL, "head": head, "sections": content},
              open(os.path.join(OUT, f"{SLUG}-content.json"), "w"), indent=1)
    open(os.path.join(OUT, f"{SLUG}-combined.css"), "w").write("\n\n".join(css_text))
    print("OK", SLUG, "sections:", len(content), "css bytes:", sum(len(c) for c in css_text))

main()
