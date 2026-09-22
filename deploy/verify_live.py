#!/usr/bin/env python3
"""
Confirm that what is on the site is byte-for-byte what the builders produced.

The host's bot-check interstitial can answer a REST write with an HTML holding
page and HTTP 200, so a push that *looked* fine can silently have written
nothing. This reads _elementor_data back for every page in deploy/pages.json
and compares it with the local template.

  python3 deploy/verify_live.py
"""
import base64, json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP = os.environ.get("WP_URL", "").rstrip("/")
AUTH = "Basic " + base64.b64encode(
    f"{os.environ.get('WP_USER','')}:{os.environ.get('WP_APP_PASSWORD','')}".encode()).decode()

# page slug -> template file stem
TEMPLATE_FOR = {
    "home-new": "home-v2",
    "contact": "contact",
    "case-studies": "case-studies",
    "london-portfolio": "case-london-portfolio",
    "bridging-holiday-let": "case-bridging-holiday-let",
    "complex-income": "case-complex-income",
}
for s in ["buy-to-let", "residential", "limited-company-buy-to-let", "hmos",
          "multi-unit-mufb", "commercial-and-semi-commercial", "bridging-finance"]:
    TEMPLATE_FOR[s] = f"service-{s}"


def get(path, tries=5):
    last = None
    for a in range(tries):
        try:
            r = urllib.request.Request(f"{WP}/wp-json{path}", method="GET")
            r.add_header("Authorization", AUTH)
            return json.loads(urllib.request.urlopen(r, timeout=90).read().decode())
        except Exception as e:      # interstitial, rate limit, transient 5xx
            last = e
            time.sleep(5 + 3 * a)
    raise SystemExit(f"could not read {path}: {last}")


if __name__ == "__main__":
    if not WP:
        sys.exit("set WP_URL, WP_USER and WP_APP_PASSWORD first")
    pages = json.load(open(os.path.join(ROOT, "deploy", "pages.json")))
    bad = []
    for slug, pid in pages.items():
        tpl = TEMPLATE_FOR.get(slug)
        if not tpl:
            print(f"  ?  {slug:34s} no template mapped, skipped")
            continue
        path = os.path.join(ROOT, "templates", f"{tpl}.json")
        want = json.dumps(json.load(open(path))["content"], separators=(",", ":"))
        got = get(f"/wp/v2/pages/{pid}?context=edit")["meta"].get("_elementor_data", "")
        ok = got == want
        print(f"  {'ok' if ok else 'NO':>2s} {slug:34s} live {len(got):>7d}  local {len(want):>7d}")
        if not ok:
            bad.append(slug)
        time.sleep(2)
    print()
    print("all pages match" if not bad else f"STALE: {', '.join(bad)}")
    sys.exit(1 if bad else 0)
