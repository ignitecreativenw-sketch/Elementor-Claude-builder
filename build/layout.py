#!/usr/bin/env python3
"""
Shared layout helpers (extracted from the Expert Broker build, Sept 2026).

    from layout import boxed2, row, col, eyebrow, h2, stars, tick_line, center_on_mobile
    from layout import SITE          # contact details, loaded from spec/site.json

Rules baked in (each one was a real fault on a real build):
  * row() stays horizontal until mobile; col(w_t=100) only stacks if the parent
    row stacks at tablet too — audit_widths.py checks every template for this.
  * boxed2() keeps a 24px gutter at every breakpoint (MAXW2 = content + 48).
  * mobile_extra (<=880) values are emitted; Elementor ignores them until the
    Mobile Landscape breakpoint is on — deploy/set_breakpoints.py --apply.
  * SITE["phone"], SITE["phone_tel"], SITE["email"] come from spec/site.json and
    the import fails loudly if any is missing or still a placeholder, so a form
    can never ship addressed to nobody.
"""
import json, os, re, sys
from build_template import (
    px, gap, pad, responsive, typo, media, link, container, widget, eid,
    heading, text, image, button, icon_list, boxed,
    PRIMARY, NAVY, SURFACE, TEXT, WHITE, MUTED, FONT, ELEMENTOR_VERSION,
    TEMPLATES,
)

INK      = "#0A1551"   # PER SITE — headings / body on light
BODY     = "#4A5378"   # PER SITE — secondary copy
LINE     = "#E3E6EF"
FOOT_TXT = "#D7DDF0"
FOOT_DIM = "#98A2C4"
GOLD     = "#E8B93F"
MAXW2    = 1288        # 1240 of content + 24px gutter each side

# ---------------------------------------------------------------- site contact details (required)
_SITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "spec", "site.json")
def _load_site():
    try:
        s = json.load(open(_SITE_PATH))
    except FileNotFoundError:
        sys.exit("spec/site.json missing — copy spec/site.example.json and fill in phone, email, form_recipient")
    for k in ("phone", "phone_tel", "email", "form_recipient"):
        v = str(s.get(k, "")).strip()
        if not v or re.search(r"\[|PLACEHOLDER|REPLACE|example\.com", v, re.I):
            sys.exit(f"spec/site.json: '{k}' is missing or still a placeholder ({v!r}) — collect it at intake")
    return s
SITE = _load_site()
PHONE, PHONE_TEL, EMAIL = SITE["phone"], SITE["phone_tel"], SITE["email"]

def boxed2(**kw):
    """Section-level boxed container.

    Sections used to carry 0 horizontal padding on desktop and 24px only from
    tablet down, so between 1025px and the boxed width the content sat flush
    against both screen edges (very visible on iPad Air / iPad Pro landscape).
    Every section now keeps a 24px gutter at every breakpoint; MAXW2 was raised
    by the same 48px so the desktop content width is unchanged at 1240.
    """
    s = {"content_width": "boxed", "boxed_width": px(MAXW2)}
    s.update(kw)
    p = s.get("padding")
    if isinstance(p, dict) and p.get("unit") == "px":
        if p.get("right") in ("0", 0):
            p["right"] = "24"
        if p.get("left") in ("0", 0):
            p["left"] = "24"
    return s


def row(children, seed, **kw):
    base = dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "column"),
        **responsive("flex_align_items", "flex-start"),
        **gap(32, 28, 24),
        **pad((0, 0, 0, 0), (0, 24, 0, 24), (0, 0, 0, 0)),
    )
    base.update(kw)
    return container(children, seed=seed, inner=True, **base)


def col(children, seed, w=None, w_t=None, w_m=None, align="flex-start", g=(20, 18, 16), **kw):
    base = dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", align),
        **gap(*g),
        **pad((0, 0, 0, 0), (0, 24, 0, 24), (0, 0, 0, 0)),
    )
    if w is not None:
        base.update(responsive("width", px(w, "%"), px(w_t or w, "%"), px(w_m or 100, "%")))
    base.update(kw)
    return container(children, seed=seed, inner=True, **base)


def _half_on_mobile(w, pct=49):
    """Two buttons side by side on mobile instead of stacked full-width.

    At half of a ~302px column the default 14px label plus 24px of side
    padding wraps onto two lines, so the mobile type and padding are
    tightened here too — 13px inside 10px padding keeps
    "Request a callback" on one line.
    """
    s = w["settings"]
    s["_element_width"] = "initial"
    s["_element_custom_width_mobile"] = px(pct, "%")
    s["align_mobile"] = "center"
    s["typography_font_size_mobile"] = px(12)
    s["typography_letter_spacing_mobile"] = px(-0.3)
    s["text_padding_mobile"] = {"unit": "px", "top": "15", "right": "8",
                                "bottom": "15", "left": "8", "isLinked": False}
    return w


def _fill_on_mobile(w):
    """Button fills the column it sits in (the column is already half-width)."""
    s = w["settings"]
    s["_element_width"] = "initial"
    s["_element_custom_width_mobile"] = px(100, "%")
    s["align_mobile"] = "center"
    s["typography_font_size_mobile"] = px(13)
    s["typography_letter_spacing_mobile"] = px(-0.2)
    s["text_padding_mobile"] = {"unit": "px", "top": "15", "right": "10",
                                "bottom": "15", "left": "10", "isLinked": False}
    return w



def _tappable(w):
    """Footer link rows were ~24px tall — under the 44px touch guideline.

    Native fix: a taller line-height at tablet/mobile (the icon-list anchor is
    as tall as its line box) plus a little more space between items.
    """
    s = w["settings"]
    s["space_between"] = px(6)
    s["space_between_tablet"] = px(10)
    s["space_between_mobile"] = px(10)
    s["typography_line_height_tablet"] = px(2.1, "em")
    s["typography_line_height_mobile"] = px(2.1, "em")
    return w


def _hide_on_mobile(w):
    w["settings"]["hide_mobile"] = "hidden-mobile"
    return w


def _show_only_mobile(w):
    """Visible on mobile only — the desktop/tablet equivalent sits elsewhere."""
    w["settings"]["hide_desktop"] = "hidden-desktop"
    w["settings"]["hide_tablet"] = "hidden-tablet"
    return w


def _center_on_mobile_widget(w):
    w["settings"]["align_mobile"] = "center"
    return w


def eyebrow(label, color=PRIMARY, align="left", seed="eyebrow"):
    return text(f"<p>{label}</p>", color=color, align=align,
                size=(14, 14, 14), lh=1.4, weight="700", seed=seed)


def h2(title, color=INK, align="left", seed="h2"):
    return heading(title, tag="h2", color=color, align=align,
                   size=(40, 34, 28), lh=1.2, ls=-1.0, seed=seed)


def stars(size=16, seed="stars"):
    return widget("star-rating", {
        "rating": 5, "star_style": "star_unicode", "unmarked_star_style": "solid",
        "stars_color": GOLD, "unmarked_star_color": "#E0E0E0",
        **responsive("icon_size", px(size)),
        "star_space": px(2), **responsive("align", "left"), "title": "",
    }, seed)


def tick_line(label, color=INK, seed="tick"):
    return widget("icon-list", {
        "icon_list": [{
            "text": label,
            "selected_icon": {"value": "fas fa-check", "library": "fa-solid"},
            "link": {"url": ""}, "_id": eid("tick"),
        }],
        "space_between": px(0), "text_color": color, "icon_color": PRIMARY,
        **responsive("icon_size", px(17)),
        **typo(FONT, 16, 15.5, 15, "400", 1.55),
    }, seed)


# ---------------------------------------------------------------- mobile
# Widgets carry their alignment per breakpoint, so rather than hand-editing
# every call site, walk the finished tree and add the mobile values. Applied
# to pages and the footer; NOT to the header, whose mobile row is logo-left /
# burger-right by design, and not to form fields, where centred labels and
# input text read badly.
_ALIGN_WIDGETS = {"heading", "text-editor", "button", "image", "icon",
                  "star-rating", "icon-list", "social-icons", "divider"}


def center_on_mobile(node):
    if isinstance(node, list):
        for n in node:
            center_on_mobile(n)
        return node
    s = node.get("settings", {})
    t = node.get("elType")
    if t == "container":
        # setdefault, not assignment: a block that has deliberately asked for
        # a different mobile cross-axis value (e.g. "stretch" so a pair of
        # side-by-side buttons come out the same height) keeps it.
        s.setdefault("flex_align_items_mobile", "center")
        if s.get("flex_direction_mobile") == "column":
            s["flex_justify_content_mobile"] = "flex-start"
    elif t == "widget":
        w = node.get("widgetType")
        if w in _ALIGN_WIDGETS:
            s["align_mobile"] = "center"
        elif w == "image-box":
            s["text_align_mobile"] = "center"
        elif w == "accordion":
            s["title_alignment_mobile"] = "center"
        elif w == "form":
            s["button_align_mobile"] = "center"   # button only, not the fields
    for c in node.get("elements", []):
        center_on_mobile(c)
    return node


# ---------------------------------------------------------------- header
