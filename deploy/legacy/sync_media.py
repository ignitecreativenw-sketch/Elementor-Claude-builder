#!/usr/bin/env python3
"""
Build deploy/media-map.json, uploading only what the library is missing.

Split out of push_rest.py because the host sits behind a bot-protection layer
that starts returning an HTML "One moment, please..." interstitial when the
REST API is hit hard. This paces the requests, retries the interstitial with
backoff, and only touches alt text when it is actually wrong — so a re-run
after a wobble is cheap.

  WP_URL=... WP_USER=... WP_APP_PASSWORD=... python3 deploy/sync_media.py
"""
import base64, json, mimetypes, os, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP = os.environ["WP_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(
    f'{os.environ["WP_USER"]}:{os.environ["WP_APP_PASSWORD"]}'.encode()).decode()

PACE = float(os.environ.get("PACE", "0.7"))     # seconds between calls
TRIES = 6


class Interstitial(Exception):
    pass


def call(method, path, body=None, raw=None, headers=None, timeout=180):
    url = path if path.startswith("http") else f"{WP}/wp-json{path}"
    for attempt in range(1, TRIES + 1):
        data = raw if raw is not None else (
            json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", AUTH)
        req.add_header("User-Agent", "teb-deploy/1.0")
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
                raise Interstitial(txt[:120])
        except (Interstitial, urllib.error.URLError) as e:
            if isinstance(e, urllib.error.HTTPError) and e.code not in (429, 502, 503, 520, 521):
                raise SystemExit(f"{method} {url} -> {e.code}\n"
                                 f"{e.read().decode()[:500]}")
            wait = min(60, 5 * attempt * attempt)
            print(f"   ... {method} {path.split('?')[0]} blocked, "
                  f"retry {attempt}/{TRIES} in {wait}s")
            time.sleep(wait)
    raise SystemExit(f"{method} {url} -> gave up after {TRIES} tries")


def library():
    out, page = {}, 1
    while True:
        batch = call("GET", f"/wp/v2/media?per_page=100&page={page}"
                            f"&_fields=id,slug,source_url,alt_text")
        if not batch:
            break
        for m in batch:
            out[m["slug"]] = m
        if len(batch) < 100:
            break
        page += 1
        time.sleep(PACE)
    return out


def main():
    manifest = {os.path.splitext(a["file"])[0]: a["alt"]
                for a in json.load(open(os.path.join(ROOT, "assets",
                                                     "manifest.json")))}
    existing = library()
    print(f"   library: {len(existing)} attachments")

    assets = os.path.join(ROOT, "assets")
    files = sorted(f for f in os.listdir(assets) if f.endswith(".webp"))
    media_map, uploaded, fixed = {}, 0, 0

    for fn in files:
        stem = os.path.splitext(fn)[0]
        alt = manifest.get(stem, "")
        m = existing.get(stem)
        if m is None:
            blob = open(os.path.join(assets, fn), "rb").read()
            ctype = mimetypes.guess_type(fn)[0] or "image/webp"
            m = call("POST", "/wp/v2/media", raw=blob, headers={
                "Content-Type": ctype,
                "Content-Disposition": f'attachment; filename="{fn}"',
            })
            uploaded += 1
            print(f"   + {fn} -> #{m['id']}")
            time.sleep(PACE)
        current = (m.get("alt_text") or "")
        if alt and current != alt:
            call("POST", f"/wp/v2/media/{m['id']}",
                 body={"alt_text": alt, "title": alt[:90]})
            fixed += 1
            time.sleep(PACE)
        media_map[fn] = {"id": m["id"], "url": m["source_url"], "alt": alt}

    out = os.path.join(ROOT, "deploy", "media-map.json")
    json.dump(media_map, open(out, "w"), indent=1)
    print(f"   media-map.json: {len(media_map)} attachments "
          f"({uploaded} uploaded, {fixed} alt fixed)")


if __name__ == "__main__":
    main()
