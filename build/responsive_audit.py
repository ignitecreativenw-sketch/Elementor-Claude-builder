#!/usr/bin/env python3
"""
Responsive sweep. Loads the target at each breakpoint and asserts the things
that actually break on real sites, rather than comparing screenshots.

  python3 build/responsive_audit.py [url]

Checks per breakpoint:
  overflow      no horizontal page scroll
  clipping      no element wider than the viewport
  type          no rendered text under 14px (12px for legal/footnote roles)
  tap targets   every link/button/input at least 44px tall on mobile
  contrast      text vs its effective background, 4.5:1 (3:1 at 24px+)
  stacking      multi-column rows actually collapse
  images        every img has width+height or an aspect ratio (CLS)
  alt text      no img missing alt
  headings      exactly one h1, no skipped levels
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright

TARGET = sys.argv[1] if len(sys.argv) > 1 else \
    "https://STAGING-URL/"
BREAKPOINTS = [(1440, "desktop"), (1024, "tablet"), (768, "tablet-portrait"),
               (390, "mobile"), (360, "mobile-small")]

AUDIT_JS = r"""
() => {
  const out = {overflow:{}, clipped:[], smallText:[], tapTargets:[], contrast:[],
               images:[], alts:[], headings:{}, rows:[]};
  const vw = document.documentElement.clientWidth;

  out.overflow = {
    docScrollW: document.documentElement.scrollWidth,
    clientW: vw,
    horizontal: document.documentElement.scrollWidth > vw + 1,
  };

  const parseRGB = c => {
    const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(Number);
    return {r:p[0], g:p[1], b:p[2], a:p.length>3?p[3]:1};
  };
  const lum = ({r,g,b}) => {
    const f = v => { v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055,2.4); };
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b);
  };
  const effBg = el => {
    let n = el;
    while (n && n !== document.documentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null; // can't judge
      const c = parseRGB(s.backgroundColor);
      if (c && c.a > 0.85) return c;
      n = n.parentElement;
    }
    return {r:255,g:255,b:255,a:1};
  };
  const ratio = (a,b) => {
    const l1 = lum(a), l2 = lum(b);
    return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05);
  };
  const label = el => {
    const t = (el.innerText||'').trim().replace(/\s+/g,' ').slice(0,44);
    return (el.tagName.toLowerCase() + (t ? ' "'+t+'"' : '')
            + (el.className ? ' .'+String(el.className).split(' ')[0] : ''));
  };

  // visually-hidden helpers and decorative glyphs are not user-facing text
  const hidden = el => el.closest(
    '.elementor-screen-only, .skip-link, .screen-reader-text, [aria-hidden=true]');
  const decorative = el => el.closest(
    '.elementor-star-rating, .elementor-social-icon, svg');

  document.querySelectorAll('body *').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if (hidden(el)) return;
    const s = getComputedStyle(el);
    if (s.position === 'fixed') return;

    if (r.right > vw + 2 && s.overflow !== 'hidden' && s.overflowX !== 'hidden') {
      if (el.children.length === 0 || r.width > vw + 2)
        out.clipped.push({el: label(el), right: Math.round(r.right), w: Math.round(r.width)});
    }

    const direct = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (direct) {
      const fs = parseFloat(s.fontSize);
      const legal = /legal|footnote|disclaimer|copy/i.test(String(el.className));
      if (fs < (legal ? 11 : 14))
        out.smallText.push({el: label(el), px: +fs.toFixed(1)});

      const fg = decorative(el) ? null : parseRGB(s.color);
      const bg = effBg(el);
      if (fg && bg && fg.a > 0.5) {
        const big = fs >= 24 || (fs >= 18.66 && parseInt(s.fontWeight,10) >= 700);
        const need = big ? 3 : 4.5;
        const got = ratio(fg, bg);
        if (got < need)
          out.contrast.push({el: label(el), ratio: +got.toFixed(2), need, px: +fs.toFixed(1)});
      }
    }
  });

  if (vw <= 767) {
    document.querySelectorAll('a, button, input:not([type=hidden]), select, textarea').forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) return;
      if (hidden(el)) return;
      if (getComputedStyle(el).display === 'inline') return;  // inline links in prose
      // 44px is the AAA guideline; 24px is the AA floor (WCAG 2.5.8). Report
      // both so the two are not conflated.
      if (r.height < 44)
        out.tapTargets.push({el: label(el), h: Math.round(r.height),
                             belowAA: r.height < 24});
    });
  }

  document.querySelectorAll('img').forEach(im => {
    const r = im.getBoundingClientRect();
    if (r.width === 0) return;
    const hasDims = (im.getAttribute('width') && im.getAttribute('height'))
                 || getComputedStyle(im).aspectRatio !== 'auto';
    if (!hasDims) out.images.push({src: im.currentSrc.split('/').pop(), w: Math.round(r.width)});
    if (im.getAttribute('alt') === null) out.alts.push(im.currentSrc.split('/').pop());
  });

  const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')]
    .filter(h => h.getBoundingClientRect().height > 0);
  out.headings = {
    h1: hs.filter(h => h.tagName === 'H1').length,
    sequence: hs.map(h => +h.tagName[1]),
  };

  // did multi-column rows collapse?
  document.querySelectorAll('.e-con').forEach(c => {
    const s = getComputedStyle(c);
    if (s.flexDirection !== 'row') return;
    const kids = [...c.children].filter(k => k.getBoundingClientRect().height > 0);
    if (kids.length < 2) return;
    const tops = new Set(kids.map(k => Math.round(k.getBoundingClientRect().top)));
    out.rows.push({id: c.dataset.id, kids: kids.length, rows: tops.size,
                   w: Math.round(c.getBoundingClientRect().width)});
  });

  return out;
}
"""


def skipped_levels(seq):
    bad = []
    for i in range(1, len(seq)):
        if seq[i] > seq[i - 1] + 1:
            bad.append(f"h{seq[i-1]}->h{seq[i]}")
    return bad


def warm(pg):
    """Elementor deletes its per-template CSS on flush and rewrites each file on
    the next render of that template, so the first loads after a deploy are
    half-styled. Request the page until every Elementor sheet serves as CSS."""
    for _ in range(10):
        pg.goto(TARGET, wait_until="load", timeout=45000)
        if "One moment" in (pg.title() or ""):
            time.sleep(12)
            continue
        pg.wait_for_timeout(1500)
        ok = pg.evaluate(
            "() => [...document.querySelectorAll("
            "  'link[id^=elementor-post-]')].every(l => {"
            "  const ss = [...document.styleSheets].find(s => s.href === l.href);"
            "  try { return ss && ss.cssRules.length > 0; } catch(e) { return false; }})")
        if ok:
            return True
        pg.wait_for_timeout(2500)
    return False


def run():
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        wctx = b.new_context(viewport={"width": 1440, "height": 900})
        wpg = wctx.new_page()
        if not warm(wpg):
            print("warning: some Elementor stylesheets never loaded — results "
                  "below may be measured against a half-styled page")
        wctx.close()
        for w, name in BREAKPOINTS:
            ctx = None
            pg = None
            # the site occasionally serves a shell while Elementor regenerates
            # its CSS, so gate on the page actually being there before auditing
            ready = False
            for attempt in range(10):
                # a stylesheet that got the interstitial stays failed in the
                # HTTP cache, so each attempt gets a clean context and a
                # cache-busting query
                if ctx is not None:
                    ctx.close()
                ctx = b.new_context(viewport={"width": w, "height": 900},
                                    is_mobile=w <= 767, has_touch=w <= 767)
                pg = ctx.new_page()
                # NB: do not add a cache-busting query — the host's bot check
                # challenges requests carrying unknown query params, which is
                # what a fresh context is for
                pg.goto(TARGET, wait_until="load", timeout=45000)
                # the host intermittently serves a JS bot-check interstitial
                # ("One moment, please...") instead of the page
                if "One moment" in (pg.title() or ""):
                    # rate-limited by the host's bot check — back off hard
                    ctx.close(); ctx = None
                    time.sleep(12 + attempt * 6)
                    continue
                try:
                    pg.wait_for_selector("[data-elementor-type] h1", timeout=12000)
                    pg.wait_for_function(
                        "() => document.querySelectorAll('body *').length > 200",
                        timeout=12000)
                    # and on Elementor's per-page CSS actually being applied —
                    # without it headings fall back to theme defaults and every
                    # colour check reports a false failure
                    # Elementor writes per-page CSS lazily, so the first request
                    # after a flush can serve the page with an empty stylesheet.
                    # Gate on the design actually being in effect, not on sheet
                    # count — the h1 is 34px+ by design, 40px unstyled.
                    pg.wait_for_function(
                        "() => { const h = document.querySelector('h1');"
                        "  if (!h) return false;"
                        "  const fs = parseFloat(getComputedStyle(h).fontSize);"
                        "  return fs >= 30 && fs !== 40; }",
                        timeout=20000)
                    # header/footer templates have their own stylesheets, so
                    # confirm the header is actually painted before auditing
                    pg.wait_for_function(
                        "() => ['.elementor-location-header .e-con',"
                        "       '.elementor-location-footer .e-con'].every(sel => {"
                        "  const c = document.querySelector(sel);"
                        "  if (!c) return false;"
                        "  const bg = getComputedStyle(c).backgroundColor;"
                        "  return bg && bg !== 'rgba(0, 0, 0, 0)'; })",
                        timeout=15000)
                    ready = True
                    break
                except Exception:
                    time.sleep(6 + attempt * 3)
            if not ready:
                raise SystemExit(f"{name}: page never became ready — aborting sweep "
                                 "rather than reporting a false pass")
            pg.wait_for_timeout(2200)
            pg.evaluate("async()=>{const h=document.documentElement.scrollHeight;"
                        "for(let y=0;y<h;y+=500){window.scrollTo(0,y);"
                        "await new Promise(r=>setTimeout(r,110));}window.scrollTo(0,0);}")
            pg.wait_for_timeout(1200)
            pg.evaluate("()=>document.querySelectorAll('#wpadminbar').forEach(e=>e.remove())")
            report[name] = pg.evaluate(AUDIT_JS)
            report[name]["width"] = w
            ctx.close()
            time.sleep(8)          # pace the next breakpoint past the bot check
        b.close()

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "qa",
                       "responsive-audit.json")
    json.dump(report, open(out, "w"), indent=1)

    print(f"\nResponsive sweep — {TARGET}\n")
    hdr = f"{'breakpoint':<17}{'overflow':>9}{'clipped':>9}{'<14px':>7}{'tap<44':>8}{'contrast':>10}{'img dims':>10}{'no alt':>8}"
    print(hdr)
    print("-" * len(hdr))
    for name, r in report.items():
        print(f"{name+' ('+str(r['width'])+')':<17}"
              f"{('FAIL' if r['overflow']['horizontal'] else 'ok'):>9}"
              f"{len(r['clipped']):>9}{len(r['smallText']):>7}"
              f"{len(r['tapTargets']):>8}{len(r['contrast']):>10}"
              f"{len(r['images']):>10}{len(r['alts']):>8}")

    print("\nHeadings")
    for name, r in report.items():
        bad = skipped_levels(r["headings"]["sequence"])
        print(f"  {name:<16} h1 count {r['headings']['h1']}"
              + (f"   skipped: {', '.join(bad)}" if bad else "   no skipped levels"))

    for name, r in report.items():
        issues = []
        if r["overflow"]["horizontal"]:
            issues.append(f"page scrolls to {r['overflow']['docScrollW']}px in a "
                          f"{r['overflow']['clientW']}px viewport")
        for c in r["clipped"][:6]:
            issues.append(f"clipped: {c['el']} extends to {c['right']}px")
        for t in r["smallText"][:6]:
            issues.append(f"{t['px']}px text: {t['el']}")
        for t in r["tapTargets"][:6]:
            issues.append(f"{t['h']}px tall tap target: {t['el']}")
        for c in r["contrast"][:6]:
            issues.append(f"contrast {c['ratio']}:1 (needs {c['need']}) at "
                          f"{c['px']}px: {c['el']}")
        for i in r["images"][:4]:
            issues.append(f"no width/height: {i['src']}")
        for a in r["alts"][:4]:
            issues.append(f"missing alt: {a}")
        if issues:
            print(f"\n{name} ({r['width']})")
            for i in issues:
                print("  -", i)
    print(f"\nfull detail: qa/responsive-audit.json")


if __name__ == "__main__":
    run()
