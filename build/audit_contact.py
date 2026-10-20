#!/usr/bin/env python3
"""
Check every template for missing or broken contact details.

  python3 build/audit_contact.py

Three faults it catches, all of which render perfectly well and are only
noticed by a visitor who tries to use them:

  placeholder   a [PHONE NUMBER] / [EMAIL ADDRESS] token still in the output
  dead tel:     a button whose label is the phone number but whose href is the
                bare string "tel:" — it looks right and does nothing when tapped
  form sink     a form widget whose email_to is a placeholder, so submissions
                are addressed to nobody
  em-dash       an em-dash (U+2014) in copy on a `mode: redesign` or `mode: new`
                page (CONFLICTS.md #7). Clone pages reproduce the reference text
                and are exempt; the mode is read from spec/<page>.md.

Exit status is non-zero when anything is found, so it can gate a push.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")

PLACEHOLDER = re.compile(r"\[(PHONE NUMBER|EMAIL ADDRESS|CLIENT TO [A-Z ]+)\]")
# a tel: link with nothing after the colon
DEAD_TEL = re.compile(r'tel:(?![0-9+])')
EM_DASH = "\u2014"
SPEC = os.path.join(ROOT, "spec")


def page_mode(name):
    """mode: clone|redesign|new from spec/<name>.md; 'new' when there is no spec."""
    path = os.path.join(SPEC, f"{name}.md")
    if not os.path.exists(path):
        return "new"
    m = re.search(r"^mode:\s*(clone|redesign|new)", open(path, encoding="utf-8").read(), re.M)
    return m.group(1) if m else "new"


def walk(node, path, out, check_dash=False):
    s = node.get("settings", {})
    wtype = node.get("widgetType") or node.get("elType")

    for key, value in s.items():
        if isinstance(value, str):
            if check_dash and EM_DASH in value:
                out.append((path, wtype, "em-dash", f"in {key}: {value[:50]!r}"))
            for m in PLACEHOLDER.findall(value):
                # bracketed client copy is deliberate in post bodies and in the
                # service criteria tables; only contact details are a fault here
                if m in ("PHONE NUMBER", "EMAIL ADDRESS"):
                    out.append((path, wtype, "placeholder", f"[{m}] in {key}"))
            if DEAD_TEL.search(value):
                out.append((path, wtype, "dead tel:", f"{key} = {value[:40]!r}"))
        elif isinstance(value, dict) and isinstance(value.get("url"), str):
            url = value["url"]
            if url.startswith("tel:") and DEAD_TEL.search(url):
                out.append((path, wtype, "dead tel:", f"{key} url is {url!r}"))

    if wtype == "form":
        to = s.get("email_to", "")
        if not to or PLACEHOLDER.search(str(to)):
            out.append((path, wtype, "form sink", f"email_to = {to!r}"))

    for i, kid in enumerate(node.get("elements", [])):
        walk(kid, f"{path}/{i}", out, check_dash)


def main():
    names = sys.argv[1:] or sorted(
        os.path.splitext(f)[0] for f in os.listdir(TEMPLATES) if f.endswith(".json"))
    total = 0
    for name in names:
        doc = json.load(open(os.path.join(TEMPLATES, f"{name}.json")))
        out = []
        check_dash = page_mode(name) != "clone"
        for i, sec in enumerate(doc["content"]):
            walk(sec, f"[{i}]", out, check_dash)
        if not out:
            print(f"  ok    {name}")
            continue
        total += len(out)
        seen = set()
        for path, wtype, kind, detail in out:
            key = (name, kind, detail)
            if key in seen:
                continue
            seen.add(key)
            print(f"  FAIL  {name} [{kind}] {wtype} at {path}: {detail}")
    print(f"\n{len(names)} templates, {total} contact-detail problems")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
