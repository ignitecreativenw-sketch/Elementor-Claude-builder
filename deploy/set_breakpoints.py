#!/usr/bin/env python3
"""
Turn on Elementor's Mobile Landscape (<=880) breakpoint on the target site.

The build now emits *_mobile_extra values (hero, service body, contact main,
CTA and the three card grids stack there instead of at 1024). Elementor ignores
those keys unless the breakpoint is active, so this has to run once before the
pages are pushed.

  export WP_URL=https://STAGING-URL
  export WP_USER=...
  export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'
  python3 deploy/set_breakpoints.py            # show current
  python3 deploy/set_breakpoints.py --apply    # write

If the REST route refuses (Elementor does not always register the kit's
settings meta), do it by hand instead — it is one toggle:
  Elementor editor > hamburger > Site Settings > Layout > Breakpoints
  > enable "Mobile Landscape" (leave it at 880) > Update.
"""
import base64, json, os, sys, urllib.request, urllib.error

WP = os.environ.get("WP_URL", "").rstrip("/")
USER = os.environ.get("WP_USER", "")
APP = os.environ.get("WP_APP_PASSWORD", "")
if not (WP and USER and APP):
    sys.exit("set WP_URL, WP_USER and WP_APP_PASSWORD first")
AUTH = "Basic " + base64.b64encode(f"{USER}:{APP}".encode()).decode()

WANT = ["viewport_mobile", "viewport_mobile_extra", "viewport_tablet"]


def call(method, path, body=None):
    url = f"{WP}/wp-json{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", AUTH)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt.strip() else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url} -> {e.code}\n{e.read().decode()[:500]}")


def find_kit():
    items = call("GET", "/wp/v2/elementor_library?per_page=100&context=edit")
    for it in items:
        meta = it.get("meta", {})
        if meta.get("_elementor_template_type") == "kit":
            return it
    sys.exit("no kit found over REST — use the Site Settings toggle instead "
             "(see the docstring)")


kit = find_kit()
raw = kit.get("meta", {}).get("_elementor_page_settings") or "{}"
settings = json.loads(raw) if isinstance(raw, str) else raw
current = settings.get("active_breakpoints", ["viewport_mobile", "viewport_tablet"])
print("kit id:", kit["id"])
print("active_breakpoints now:", current)

if "--apply" not in sys.argv:
    print("\nrun again with --apply to set:", WANT)
    raise SystemExit

settings["active_breakpoints"] = WANT
settings.setdefault("viewport_mobile_extra", 880)
call("POST", f"/wp/v2/elementor_library/{kit['id']}",
     {"meta": {"_elementor_page_settings": json.dumps(settings)}})
call("DELETE", "/elementor/v1/cache")

check = find_kit()
raw2 = check.get("meta", {}).get("_elementor_page_settings") or "{}"
now = (json.loads(raw2) if isinstance(raw2, str) else raw2).get("active_breakpoints")
print("active_breakpoints after:", now)
if now != WANT:
    sys.exit("write did not stick — use the Site Settings toggle by hand")
print("done — now push the pages")
