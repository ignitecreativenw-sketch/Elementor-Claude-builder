#!/usr/bin/env python3
"""
Catch the overflow bug the hard way — in the template, not the browser.

  python3 build/audit_widths.py                 # every template
  python3 build/audit_widths.py about services  # named ones

The fault it finds: a container running in `row` direction at some breakpoint
whose children's percentage widths add up to more than 100% at that same
breakpoint. It happens because `col(w=56, w_t=100)` means "full width at
tablet", which is only true if the parent row also stacks at tablet — and
`row()` defaults to staying horizontal until mobile. Two full-width columns in
a horizontal row is 200%, and the page scrolls sideways.

Checking the JSON beats screenshotting because it is exact, instant, and does
not care whether the host's bot protection feels like serving us the page.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")
BPS = [("desktop", ""), ("tablet", "_tablet"), ("mobile", "_mobile")]


def at(settings, key, suffix):
    """Elementor's cascade: mobile falls back to tablet, tablet to desktop."""
    chain = {"": [""], "_tablet": ["_tablet", ""],
             "_mobile": ["_mobile", "_tablet", ""]}[suffix]
    for s in chain:
        v = settings.get(key + s)
        if v not in (None, ""):
            return v
    return None


def hidden(node, suffix):
    """Elementor's responsive visibility. A column hidden at this breakpoint
    takes no space, so it must not count towards the row's total."""
    s = node.get("settings", {})
    flag = {"": "hide_desktop", "_tablet": "hide_tablet",
            "_mobile": "hide_mobile"}[suffix]
    return bool(s.get(flag))


def pct_width(node, suffix):
    """A child's width as a percentage, or None if it is not set in %."""
    s = node.get("settings", {})
    for key in ("width", "_element_custom_width"):
        v = at(s, key, suffix)
        if isinstance(v, dict) and v.get("unit") == "%" and v.get("size") not in (None, ""):
            return float(v["size"])
    return None


def walk(node, path, suffix, out):
    s = node.get("settings", {})
    kids = node.get("elements", [])
    if node.get("elType") == "container" and kids:
        direction = at(s, "flex_direction", suffix) or "column"
        wrap = at(s, "flex_wrap", suffix)
        if direction == "row" and wrap != "wrap":
            visible = [k for k in kids if not hidden(k, suffix)]
            widths = [pct_width(k, suffix) for k in visible]
            if any(w is not None for w in widths):
                total = sum(w for w in widths if w is not None)
                if total > 100.5:
                    out.append({
                        "path": path,
                        "id": node["id"],
                        "total": round(total, 1),
                        "children": [(k["id"], w) for k, w in zip(visible, widths)],
                    })
    for i, k in enumerate(kids):
        walk(k, f"{path}/{i}", suffix, out)


def audit(name):
    doc = json.load(open(os.path.join(TEMPLATES, f"{name}.json")))
    problems = {}
    for label, suffix in BPS:
        out = []
        for i, sec in enumerate(doc["content"]):
            walk(sec, f"[{i}]", suffix, out)
        if out:
            problems[label] = out
    return problems


def main():
    names = sys.argv[1:] or sorted(
        os.path.splitext(f)[0] for f in os.listdir(TEMPLATES) if f.endswith(".json"))
    bad = 0
    for name in names:
        problems = audit(name)
        if not problems:
            print(f"  ok    {name}")
            continue
        bad += 1
        for label, rows in problems.items():
            for r in rows:
                kids = ", ".join(f"{i}={w}%" for i, w in r["children"])
                print(f"  OVER  {name} [{label}] row {r['id']} at {r['path']} "
                      f"= {r['total']}%  ({kids})")
    print(f"\n{len(names)} templates, {bad} with row overflow")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
