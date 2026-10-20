#!/usr/bin/env python3
"""
Push through Website Core (the only way the kit connects to a site).

Website Core is Adam's WordPress plugin (v1.1.0+): one JSON endpoint, short-lived
keys with a read or write scope, no admin password, no SSH.

  python3 deploy/push_core.py <template> "<Title>" <slug> [parent-slug]
  python3 deploy/push_core.py --rotate                      # pasted key in CORE_KEY, once
  python3 deploy/push_core.py --action status
  python3 deploy/push_core.py --action '{"action":"sample","id":123}'
  python3 deploy/push_core.py --batch ops.json              # up to 50 ops, in order
  python3 deploy/push_core.py --selfdestruct                # only on Adam's explicit go-ahead

Config (deploy/.env, gitignored, never in chat):
  export CORE_URL="https://staging.example.com"          # site home from the "Copy for AI" block
  export WEBSITE_CORE_HOME="$HOME/.website-core"         # rotated key lives at $WEBSITE_CORE_HOME/<host>.key
  # export CORE_KEY="wck_..."                            # the pasted key, for the one --rotate call only

Key rule (skill rule 9): the pasted key is used ONCE, for `rotate`. The new key is
written to the key file (chmod 600); the pasted one stops working in the grace
period. Nothing here ever prints a key.

Run from Adam's Mac when the site's domain is not on the org allowlist; the cloud
container is blocked by the proxy, not by the plugin.
"""
import base64, json, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.environ.get("CORE_URL", os.environ.get("STAGING_URL", "")).rstrip("/")
HOME = os.path.expanduser(os.environ.get("WEBSITE_CORE_HOME", "~/.website-core"))
UA = "ignite-elementor-kit/2.0"
ENDPOINTS = (f"{SITE}/wp-json/website-core/v1/push",
             f"{SITE}/?rest_route=/website-core/v1/push")   # fallback when permalinks are plain
_endpoint = None


# ---------------------------------------------------------------- key
def key_path():
    host = SITE.split("//", 1)[-1].replace("/", "_")
    return os.path.join(HOME, f"{host}.key")


def load_key():
    p = key_path()
    if os.path.exists(p):
        return open(p).read().strip()
    k = os.environ.get("CORE_KEY", "").strip()
    if k:
        sys.exit("CORE_KEY is set but no rotated key exists yet: run `python3 deploy/push_core.py --rotate` first")
    sys.exit("no key: paste the site's key into CORE_KEY and run --rotate once")


def save_key(k):
    os.makedirs(HOME, mode=0o700, exist_ok=True)
    p = key_path()
    with open(p, "w") as f:
        f.write(k.strip() + "\n")
    os.chmod(p, 0o600)
    return p


# ---------------------------------------------------------------- call
BACKOFF = (5, 20, 45)
NOISY = {"status": 100000}


def call(body, key=None, timeout=180):
    """POST one action dict. Returns the decoded JSON; exits with the plugin's own error code on a hard error."""
    global _endpoint
    if not SITE:
        sys.exit("set CORE_URL (or STAGING_URL) in deploy/.env")
    key = key or load_key()
    data = json.dumps(body).encode()
    last = ""
    for attempt, wait in enumerate((0,) + BACKOFF):
        if wait:
            print(f"   ... {last} — retrying in {wait}s")
            time.sleep(wait)
        for ep in ([_endpoint] if _endpoint else ENDPOINTS):
            req = urllib.request.Request(ep, data=data, method="POST", headers={
                "Content-Type": "application/json", "X-Core-Key": key, "User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    txt = r.read().decode("utf-8", "replace")
                _endpoint = ep
            except urllib.error.HTTPError as e:
                txt = e.read().decode("utf-8", "replace")
                if e.code == 404 and not _endpoint:
                    continue                      # try the ?rest_route= form
                try:
                    err = json.loads(txt)
                except ValueError:
                    err = {"code": f"http_{e.code}", "message": txt[:300]}
                code = err.get("code", "")
                if code == "core_locked" or e.code == 429:
                    sys.exit("core_locked: too many bad attempts from this IP — wait 15 minutes")
                if code in ("core_forbidden", "core_scope", "core_expired", "core_key_expired", "core_method", "core_duplicate") or e.code in (401, 403, 405, 409):
                    sys.exit(f"{code or e.code} on {body.get('action')!r}: {err.get('message')}")
                if e.code >= 500:
                    last = f"HTTP {e.code}"
                    break
                sys.exit(f"{code or e.code} on {body.get('action')!r}: {err.get('message')}")
            except (urllib.error.URLError, TimeoutError) as e:
                last = str(e)
                break
            try:
                out = json.loads(txt)
            except ValueError:
                last = "non-JSON reply (bot-protection interstitial?)"
                break
            if isinstance(out, dict) and out.get("ok") is False and body.get("action") != "batch":
                sys.exit(f"{body.get('action')!r} failed: {json.dumps(out)[:600]}")
            return out
    sys.exit(f"gave up on {body.get('action')!r}: {last}")


def batch(ops, continue_on_error=False):
    assert len(ops) <= 50, "batch limit is 50"
    for op in ops:
        assert op.get("action") not in ("rotate", "batch", "selfdestruct"), "not allowed inside a batch"
    out = call({"action": "batch", "continue_on_error": continue_on_error, "ops": ops})
    if out.get("ok") is False:
        bad = [r for r in out.get("results", []) if isinstance(r, dict) and r.get("ok") is False]
        sys.exit(f"batch: {len(bad)} op(s) failed: {json.dumps(bad)[:800]}")
    return out


# ---------------------------------------------------------------- media
def upload_media():
    """assets/* -> media action. JPEG/PNG are converted to WebP by the plugin; the
    returned url is what goes into the JSON, never the original filename."""
    manifest = {os.path.splitext(a["file"])[0]: a["alt"]
                for a in json.load(open(os.path.join(ROOT, "assets", "manifest.json")))}
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "assets"))
                   if f.lower().endswith((".webp", ".png", ".jpg", ".jpeg", ".avif", ".gif", ".ico", ".pdf")))
    media_map = {}
    for i in range(0, len(files), 6):
        chunk = []
        for fn in files[i:i + 6]:
            stem = os.path.splitext(fn)[0]
            b = open(os.path.join(ROOT, "assets", fn), "rb").read()
            chunk.append({"name": fn, "b64": base64.b64encode(b).decode(),
                          "alt": manifest.get(stem, ""), "title": (manifest.get(stem, "") or stem)[:90],
                          "replace": os.environ.get("MEDIA_REPLACE") == "1"})
        out = call({"action": "media", "optimise": {"webp": True, "quality": 82, "max_width": 2560}, "files": chunk})
        for fn, m in out.get("media", out).items():
            if not isinstance(m, dict) or "id" not in m:
                sys.exit(f"media upload failed for {fn}: {m}")
            media_map[fn] = {"id": m["id"], "url": m["url"],
                             "alt": manifest.get(os.path.splitext(fn)[0], "")}
            opt = m.get("optimised") or {}
            print(f"   {'=' if m.get('reused') else '+'} {fn} -> #{m['id']}"
                  + (f"  ({opt.get('before')}→{opt.get('after')} {opt.get('type')})" if opt else ""))
    out = os.path.join(ROOT, "deploy", "media-map.json")
    json.dump(media_map, open(out, "w"), indent=1)
    print(f"   media-map.json: {len(media_map)} attachments")


# ---------------------------------------------------------------- build
def regenerate(tpl):
    own = os.path.join(ROOT, "build", f"build_{tpl}.py")
    if not os.path.exists(own):
        sys.exit(f"no builder for {tpl!r}: expected build/build_{tpl}.py (never a default that could overwrite a page)")
    subprocess.check_call([sys.executable, own])


# ---------------------------------------------------------------- page
def push_page(tpl, title, slug, parent=None):
    doc = json.load(open(os.path.join(ROOT, "templates", f"{tpl}.json")))
    pages_path = os.path.join(ROOT, "deploy", "pages.json")
    pages = json.load(open(pages_path)) if os.path.exists(pages_path) else {}

    body = {
        "action": "page",
        "slug": slug,
        "title": title,
        "content": doc["content"],
        "template": ("elementor_canvas" if os.environ.get("WP_CANVAS") == "1" or tpl == "landing"
                     else "elementor_header_footer"),
        "status": os.environ.get("WP_STATUS", "publish"),
    }
    if doc.get("page_settings"):
        body["elementor_settings"] = doc["page_settings"]
    if pages.get(slug):
        body["id"] = pages[slug]          # prefer id once known
    if parent:
        body["parent"] = parent           # the plugin accepts a parent slug
    if os.environ.get("SET_FRONT") == "1":
        body["set_front"] = True
    seo_path = os.path.join(ROOT, "spec", "seo", f"{slug}.json")
    if os.path.exists(seo_path):
        body["seo"] = json.load(open(seo_path))   # title, description, focus_keyword, canonical, noindex, og_image
    fi = os.environ.get("FEATURED_IMAGE")
    if fi:
        body["featured_image"] = fi

    out = call(body)
    pid = out.get("id")
    if not pid:
        sys.exit(f"page returned no id: {json.dumps(out)[:400]}")
    for w in out.get("warnings", []) or []:
        print(f"   warning: {w}")
    print(f"   page #{pid} -> {out.get('link') or out.get('url')}")
    pages[slug] = pid                     # append-only; never regenerated from an old copy
    json.dump(pages, open(pages_path, "w"), indent=1)
    return pid


# ---------------------------------------------------------------- main
def main(argv):
    if "--rotate" in argv:
        pasted = os.environ.get("CORE_KEY", "").strip()
        if not pasted:
            sys.exit("put the pasted key in CORE_KEY for this one command, then remove it from deploy/.env")
        out = call({"action": "rotate", "grace_minutes": 10}, key=pasted)
        new = out.get("key") or out.get("new_key")
        if not new:
            sys.exit(f"rotate returned no key field (got {list(out)})")
        p = save_key(new)
        print(f"   rotated; key saved to {p}; scope {out.get('scope', '?')}, expires {out.get('expires', '?')}. Remove CORE_KEY from deploy/.env now.")
        return
    if "--selfdestruct" in argv:
        if os.environ.get("CONFIRM_SELFDESTRUCT") != "yes":
            sys.exit("selfdestruct needs Adam's explicit go-ahead: CONFIRM_SELFDESTRUCT=yes")
        call({"action": "selfdestruct", "confirm": True})
        try:
            os.remove(key_path())
        except FileNotFoundError:
            pass
        print("   Website Core removed from the site; local key deleted")
        return
    if "--batch" in argv:
        ops = json.load(open(argv[argv.index("--batch") + 1]))
        out = batch(ops, continue_on_error="--continue" in argv)
        print(json.dumps(out, indent=1)[:4000])
        return
    if "--action" in argv:
        a = argv[argv.index("--action") + 1]
        body = json.loads(a) if a.startswith("{") else {"action": a}
        out = call(body)
        if body["action"] == "sample":
            path = os.path.join(ROOT, "reference", f"sample-{body.get('id', 'x')}.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            json.dump(out, open(path, "w"), indent=1)
            print(f"   wrote {path}")
        elif body["action"] == "status":
            path = os.path.join(ROOT, "reference", "status.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            out.pop("key", None)
            json.dump(out, open(path, "w"), indent=1)
            print(f"   wrote {path}")
            print(json.dumps({k: out.get(k) for k in ("wp", "elementor", "elementor_pro", "theme", "container", "seo_plugin", "front_page", "expires", "scope")}, indent=1))
        else:
            print(json.dumps(out, indent=1)[:4000])
        return

    tpl = argv[0] if argv else "home"
    title = argv[1] if len(argv) > 1 else tpl.replace("-", " ").title()
    slug = argv[2] if len(argv) > 2 else tpl
    parent = argv[3] if len(argv) > 3 else None

    for gate in ("audit_widths.py", "audit_contact.py"):
        if subprocess.call([sys.executable, os.path.join(ROOT, "build", gate)]) != 0:
            sys.exit(f"{gate} failed — fix the shared builder, then re-run")

    if os.environ.get("SKIP_MEDIA"):
        print("==> 1/4  media (skipped, media-map.json reused)")
    else:
        print("==> 1/4  media")
        upload_media()
    print("==> 2/4  regenerate template with real attachment ids and urls")
    regenerate(tpl)
    print("==> 3/4  page")
    push_page(tpl, title, slug, parent)
    print("==> 4/4  flush")
    call({"action": "flush"})
    print("   done — purge the host cache, wait 25 s, warm twice, then QA")


if __name__ == "__main__":
    main(sys.argv[1:])
