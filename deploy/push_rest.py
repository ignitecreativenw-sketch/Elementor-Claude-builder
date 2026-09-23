#!/usr/bin/env python3
"""
Push a generated Elementor template to the target site over the WP REST API.

No SSH and no FTP on this host, so everything goes over HTTPS:
  1. upload assets  -> POST /wp/v2/media          (real attachments + alt text)
  2. write media-map.json, regenerate the template with real attachment ids
  3. create/update the page -> POST /wp/v2/pages  (Elementor 4.x exposes
     _elementor_data, _elementor_edit_mode, _elementor_template_type as meta)
  4. flush Elementor CSS -> DELETE /elementor/v1/cache

Credentials come from the environment, never from a file in the repo:
  export WP_URL=https://STAGING-URL
  export WP_USER=WP-ADMIN-USER
  export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx xxxx xxxx'

  python3 deploy/push_rest.py home "Home" home
"""
import base64, json, mimetypes, os, subprocess, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP = os.environ.get("WP_URL", "").rstrip("/")
USER = os.environ.get("WP_USER", "")
APP = os.environ.get("WP_APP_PASSWORD", "")
if not (WP and USER and APP):
    sys.exit("set WP_URL, WP_USER and WP_APP_PASSWORD first")

AUTH = "Basic " + base64.b64encode(f"{USER}:{APP}".encode()).decode()
TPL = sys.argv[1] if len(sys.argv) > 1 else "home"
TITLE = sys.argv[2] if len(sys.argv) > 2 else "Home"
SLUG = sys.argv[3] if len(sys.argv) > 3 else "home"
# optional 4th arg: the slug of the parent page, so the child sits at
# /<parent>/<slug> (used by the case study detail pages)
PARENT = sys.argv[4] if len(sys.argv) > 4 else None

# pre-push gates: JSON-level auditors, exact and instant; a failure means fix the builder
for gate in ("audit_widths.py", "audit_contact.py"):
    if subprocess.call([sys.executable, os.path.join(ROOT, "build", gate)]) != 0:
        sys.exit(f"{gate} failed — fix the shared builder, then re-run")


# The host answers the REST API with a "One moment, please..." bot-protection
# interstitial when it is hit from a cloud IP, with a 200 and content-type
# text/html. It clears on its own after a few seconds, so every call backs off
# and retries rather than killing the push halfway through.
BACKOFF = (5, 20, 45, 90)
INTERSTITIAL = ("one moment, please", "request is being verified",
                "checking your browser")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def call(method, path, body=None, raw=None, headers=None, timeout=120):
    url = path if path.startswith("http") else f"{WP}/wp-json{path}"
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    last = ""
    for attempt, wait in enumerate((0,) + BACKOFF):
        if wait:
            print(f"   ... {last} — retrying in {wait}s")
            time.sleep(wait)
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", AUTH)
        req.add_header("User-Agent", UA)
        req.add_header("Accept", "application/json")
        if raw is None and body is not None:
            req.add_header("Content-Type", "application/json")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                txt = r.read().decode()
                if not txt.strip():
                    return {}
                try:
                    return json.loads(txt)
                except json.JSONDecodeError:
                    if any(m in txt.lower() for m in INTERSTITIAL):
                        last = "bot check"
                        continue
                    raise SystemExit(
                        f"{method} {url} -> non-JSON reply:\n{txt[:400]}")
        except urllib.error.HTTPError as e:
            txt = e.read().decode()
            if e.code in (403, 408, 429, 500, 502, 503, 504) and \
                    any(m in txt.lower() for m in INTERSTITIAL) or \
                    e.code in (429, 502, 503, 504):
                last = f"HTTP {e.code}"
                continue
            raise SystemExit(f"{method} {url} -> {e.code}\n{txt[:600]}")
        except (urllib.error.URLError, TimeoutError) as e:
            last = str(getattr(e, "reason", e))[:60]
            continue
    raise SystemExit(f"{method} {url} -> gave up after {len(BACKOFF)} retries "
                     f"({last}). The host's bot protection is still in the way; "
                     f"wait a minute and run it again.")


# ---------------------------------------------------------------- 1. media
def upload_media():
    manifest = {os.path.splitext(a["file"])[0]: a["alt"]
                for a in json.load(open(os.path.join(ROOT, "assets", "manifest.json")))}
    existing = {}
    page = 1
    while True:
        batch = call("GET", f"/wp/v2/media?per_page=100&page={page}&_fields=id,slug,source_url")
        if not batch:
            break
        for m in batch:
            existing[m["slug"]] = m
        if len(batch) < 100:
            break
        page += 1

    media_map = {}
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "assets")) if f.endswith(".webp"))
    for fn in files:
        stem = os.path.splitext(fn)[0]
        alt = manifest.get(stem, "")
        if stem in existing:
            m = existing[stem]
            print(f"   = {fn} (already #{m['id']})")
        else:
            blob = open(os.path.join(ROOT, "assets", fn), "rb").read()
            ctype = mimetypes.guess_type(fn)[0] or "image/webp"
            m = call("POST", "/wp/v2/media", raw=blob, headers={
                "Content-Type": ctype,
                "Content-Disposition": f'attachment; filename="{fn}"',
            })
            print(f"   + {fn} -> #{m['id']}")
        if alt:
            call("POST", f"/wp/v2/media/{m['id']}", body={"alt_text": alt, "title": alt[:90]})
        media_map[fn] = {"id": m["id"], "url": m["source_url"], "alt": alt}

    out = os.path.join(ROOT, "deploy", "media-map.json")
    json.dump(media_map, open(out, "w"), indent=1)
    print(f"   media-map.json: {len(media_map)} attachments")


# ---------------------------------------------------------------- 3. page
def push_page():
    doc = json.load(open(os.path.join(ROOT, "templates", f"{TPL}.json")))
    pages_path = os.path.join(ROOT, "deploy", "pages.json")
    pages = json.load(open(pages_path)) if os.path.exists(pages_path) else {}

    pid = pages.get(SLUG)
    if not pid:
        found = call("GET", f"/wp/v2/pages?slug={SLUG}&status=any&_fields=id")
        if found:
            pid = found[0]["id"]
    if not pid:
        pid = call("POST", "/wp/v2/pages",
                   body={"title": TITLE, "slug": SLUG, "status": "draft"})["id"]
        print(f"   created page #{pid}")
    else:
        print(f"   updating page #{pid}")

    # Elementor Canvas outputs no theme header or footer. The PPC landing page
    # carries its own slim header and minimal footer inside the template, so it
    # must not get the site chrome on top; every other page must.
    page_template = ("elementor_canvas"
                     if os.environ.get("WP_CANVAS") == "1" or TPL == "landing"
                     else "elementor_header_footer")
    # WP_STATUS=publish publishes in the same call; without it the page keeps
    # whatever status it already has (a new page is created as a draft).
    status = os.environ.get("WP_STATUS")
    body = {
        "title": TITLE,
        "template": page_template,
        "meta": {
            "_elementor_edit_mode": "builder",
            "_elementor_template_type": "wp-page",
            "_elementor_data": json.dumps(doc["content"], separators=(",", ":")),
            "_elementor_page_settings": doc.get("page_settings", {}),
        },
    }
    if status:
        body["status"] = status
    if PARENT:
        ppid = pages.get(PARENT)
        if not ppid:
            found = call("GET", f"/wp/v2/pages?slug={PARENT}&status=any&_fields=id")
            if not found:
                raise SystemExit(f"parent page '{PARENT}' does not exist yet")
            ppid = found[0]["id"]
        body["parent"] = ppid
    call("POST", f"/wp/v2/pages/{pid}", body=body)
    pages[SLUG] = pid
    json.dump(pages, open(pages_path, "w"), indent=1)
    return pid


if __name__ == "__main__":
    if os.environ.get("SKIP_MEDIA"):
        print("==> 1/4  upload media (skipped, media-map.json reused)")
    else:
        print("==> 1/4  upload media")
        upload_media()
    print("==> 2/4  regenerate template with real attachment ids")
    # A template with its own builder uses it. Without this branch a new page
    # falls through to build_template.py, which does not know the name and
    # either dies on a KeyError or — worse — writes the homepage over the
    # template. `about`, `services` and `landing` all hit this.
    LEGAL = ("privacy-notice", "complaints-procedure")
    own = os.path.join(ROOT, "build", f"build_{TPL}.py")
    if TPL in LEGAL:
        subprocess.check_call([sys.executable,
                               os.path.join(ROOT, "build", "build_legal.py"), TPL])
    elif os.path.exists(own):
        subprocess.check_call([sys.executable, own])
    else:
        subprocess.check_call([sys.executable, os.path.join(ROOT, "build",
            "build_case.py" if TPL == "case-studies" or TPL.startswith("case-")
            else "build_contact.py" if TPL == "contact"
            else "build_service.py" if TPL.startswith("service-")
            else "build_v2.py" if TPL.endswith("-v2")
            else "build_template.py"),
            *(["index"] if TPL == "case-studies"
              else [TPL.replace("case-", "", 1)] if TPL.startswith("case-")
              else [] if TPL == "contact"
              else [TPL.replace("service-", "", 1)] if TPL.startswith("service-")
              else [TPL])])
    print("==> 3/4  write the page")
    pid = push_page()
    print("==> 4/4  flush Elementor CSS")
    call("DELETE", "/elementor/v1/cache")
    print(f"done — page #{pid} at {WP}/?page_id={pid}")
