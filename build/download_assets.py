#!/usr/bin/env python3
"""Download reference images into ../assets with clean, keyworded filenames."""
import json, os, re, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "reference")
ASSETS = os.path.join(HERE, "..", "assets")
os.makedirs(ASSETS, exist_ok=True)

secs = json.load(open(os.path.join(REF, "home-sections.json")))["desktop"]
lenders = json.load(open(os.path.join(REF, "home-assets.json")))["lenders"]

# (section, index) -> (filename, width to request, alt)
NAMES = {
    (0, 0): ("hero-london-skyline", 2500),
    (1, 0): ("about-icon-1", 570), (1, 1): ("about-icon-2", 570),
    (1, 2): ("about-icon-3", 570), (1, 3): ("about-icon-4", 570),
    (2, 0): ("band-london-terraces", 2500),
    (3, 0): ("service-buy-to-let", 1000), (3, 1): ("service-residential", 1000),
    (3, 2): ("service-limited-company-buy-to-let", 1000), (3, 3): ("service-hmo", 1000),
    (3, 4): ("service-multi-unit-mufb", 1000),
    (3, 5): ("service-commercial-semi-commercial", 1000),
    (3, 6): ("service-bridging-finance", 1000),
    (3, 7): ("services-secondary-graphic", 1000),
    (4, 0): ("step-1", 300), (4, 2): ("step-2", 300), (4, 3): ("step-3", 300),
    (7, 0): ("the-expert-broker-logo", 800),
}

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60] or "asset"

def grab(url, name, width, alt):
    if "squarespace-cdn" in url:
        url = url.split("?")[0] + f"?format={width}w"
    ext = ".png" if ".png" in url.lower() else (".svg" if ".svg" in url.lower() else ".jpg")
    path = os.path.join(ASSETS, name + ext)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path, alt
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())
    return path, alt

manifest = []
for s in secs:
    for j, im in enumerate(s["images"]):
        key = (s["index"], j)
        if key not in NAMES:
            continue
        name, w = NAMES[key]
        try:
            p, alt = grab(im["src"], name, w, im["alt"] or "")
            manifest.append({"file": os.path.basename(p), "alt": alt,
                             "source": im["src"], "section": s["index"],
                             "rendered": im["rendered"]})
            print("ok", os.path.basename(p), os.path.getsize(p))
        except Exception as e:
            print("FAIL", name, e)

for l in lenders:
    name = "lender-" + slug(l["alt"])
    try:
        p, alt = grab(l["src"], name, 500, l["alt"])
        manifest.append({"file": os.path.basename(p), "alt": l["alt"],
                         "source": l["src"], "section": 6,
                         "rendered": [l["w"], l["h"]]})
        print("ok", os.path.basename(p), os.path.getsize(p))
    except Exception as e:
        print("FAIL", name, e)

json.dump(manifest, open(os.path.join(ASSETS, "manifest.json"), "w"), indent=1)
print("total", len(manifest))
