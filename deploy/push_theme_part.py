#!/usr/bin/env python3
"""
Push an Elementor Theme Builder part (header / footer) over the REST API.

Creates an elementor_library post, sets _elementor_template_type to
header|footer and _elementor_conditions to "entire site", then flushes CSS.

  python3 deploy/push_theme_part.py header
  python3 deploy/push_theme_part.py footer
"""
import base64, json, os, subprocess, sys, urllib.parse, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP = os.environ["WP_URL"].rstrip("/")
AUTH = "Basic " + base64.b64encode(
    f'{os.environ["WP_USER"]}:{os.environ["WP_APP_PASSWORD"]}'.encode()).decode()
PART = sys.argv[1] if len(sys.argv) > 1 else "header"

# Elementor's template type -> where it is allowed to display. header/footer go
# everywhere; a single-post template must be scoped to posts or it will also
# take over pages.
CONDITIONS = {
    "header": ["include/general"],
    "footer": ["include/general"],
    "single-post": ["include/singular/post"],
    "archive": ["include/archive/post"],
}
assert PART in CONDITIONS, f"unknown part {PART!r}; expected one of {list(CONDITIONS)}"

# optional 2nd arg: which generated template to load into that part
TPL = sys.argv[2] if len(sys.argv) > 2 else PART
if os.path.exists(os.path.join(ROOT, "build", f"build_{TPL}.py")):
    BUILDER, BUILD_ARGS = f"build_{TPL}.py", [TPL]
elif TPL == "single-post":
    BUILDER, BUILD_ARGS = "build_blog.py", [TPL]
elif TPL.endswith("-v2"):
    BUILDER, BUILD_ARGS = "build_v2.py", [TPL]
else:
    BUILDER, BUILD_ARGS = "build_template.py", [TPL]


def call(method, path, body=None):
    req = urllib.request.Request(f"{WP}/wp-json{path}",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 method=method)
    req.add_header("Authorization", AUTH)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    import time
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                t = r.read().decode()
                if not t.strip():
                    return {}
                try:
                    return json.loads(t)
                except json.JSONDecodeError:
                    last = f"non-JSON reply: {t[:300]}"
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} -> {e.code}\n{e.read().decode()[:600]}")
        except Exception as e:                      # transient network blip
            last = str(e)[:200]
        time.sleep(2 + attempt * 3)
        req = urllib.request.Request(f"{WP}/wp-json{path}",
                                     data=json.dumps(body).encode() if body is not None else None,
                                     method=method)
        req.add_header("Authorization", AUTH)
        if body is not None:
            req.add_header("Content-Type", "application/json")
    raise SystemExit(f"{method} {path} failed after 3 attempts: {last}")


subprocess.check_call([sys.executable, os.path.join(ROOT, "build", BUILDER), *BUILD_ARGS])
doc = json.load(open(os.path.join(ROOT, "templates", f"{TPL}.json")))
title = doc["title"]

parts_path = os.path.join(ROOT, "deploy", "theme-parts.json")
parts = json.load(open(parts_path)) if os.path.exists(parts_path) else {}
tid = parts.get(PART)
if not tid:
    # the title can contain spaces ("Single Post"), which urllib refuses to
    # send raw — quote it
    q = urllib.parse.quote(title)
    found = call("GET", f"/wp/v2/elementor_library?search={q}&status=any&_fields=id,title")
    for f in found:
        if f["title"]["rendered"].lower() == title.lower():
            tid = f["id"]
            break
if not tid:
    tid = call("POST", "/wp/v2/elementor_library",
               {"title": title, "status": "publish"})["id"]
    print(f"   created {PART} template #{tid}")
else:
    print(f"   updating {PART} template #{tid}")

call("POST", f"/wp/v2/elementor_library/{tid}", {
    "title": title,
    "status": "publish",
    "meta": {
        "_elementor_edit_mode": "builder",
        "_elementor_template_type": PART,
        "_elementor_data": json.dumps(doc["content"], separators=(",", ":")),
        "_elementor_page_settings": doc.get("page_settings", {}),
        "_elementor_conditions": CONDITIONS[PART],
    },
})
parts[PART] = tid
json.dump(parts, open(parts_path, "w"), indent=1)
call("DELETE", "/elementor/v1/cache")
print(f"   {PART} #{tid} published, condition: {CONDITIONS[PART]}")
