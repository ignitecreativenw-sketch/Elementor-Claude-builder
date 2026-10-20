#!/usr/bin/env python3
"""
Generate native Elementor (Flexbox Container) JSON from the Section Spec.

Usage:  python3 build_template.py            -> writes ../templates/home.json
Media:  ids/urls come from ../deploy/media-map.json (written by push_core.py
        after `wp media import`). Until that exists, urls fall back to
        MEDIA_BASE + filename and id 0.
"""
import json, os, hashlib, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
TEMPLATES = os.path.join(ROOT, "templates")
os.makedirs(TEMPLATES, exist_ok=True)

MEDIA_BASE = "https://REPLACE-ME/wp-content/uploads/"
ELEMENTOR_VERSION = "0.4"
PROJECT = os.environ.get("PROJECT", "site")   # seeds element ids          # verify against Adam's sample export
_MEDIA = {}
_mm = os.path.join(ROOT, "deploy", "media-map.json")
if os.path.exists(_mm):
    _MEDIA = json.load(open(_mm))

# ---------------------------------------------------------------- ids
_counter = itertools.count(1)
def eid(seed=None):
    """7-char lowercase hex, deterministic per run so diffs stay readable."""
    n = next(_counter)
    return hashlib.md5(f"{PROJECT}-{seed}-{n}".encode()).hexdigest()[:7]

# ---------------------------------------------------------------- value helpers
def px(size, unit="px"):
    return {"unit": unit, "size": size, "sizes": []}

def gap(d, t=None, m=None, me=None):
    def g(v):
        return {"unit": "px", "size": v, "column": str(v), "row": str(v), "isLinked": True}
    out = {"flex_gap": g(d)}
    if t is not None: out["flex_gap_tablet"] = g(t)
    if me is not None: out["flex_gap_mobile_extra"] = g(me)
    if m is not None: out["flex_gap_mobile"] = g(m)
    return out

def pad(d, t=None, m=None, me=None):
    """Each arg is (top, right, bottom, left) in px.

    `me` is the Mobile Landscape (<=880) breakpoint, which sits between tablet
    and mobile; omit it and tablet's value cascades down to it as before.
    """
    def p(v):
        return {"unit": "px", "top": str(v[0]), "right": str(v[1]),
                "bottom": str(v[2]), "left": str(v[3]), "isLinked": False}
    out = {"padding": p(d)}
    if t: out["padding_tablet"] = p(t)
    if me: out["padding_mobile_extra"] = p(me)
    if m: out["padding_mobile"] = p(m)
    return out

def responsive(key, d, t=None, m=None, me=None):
    """Always writes every key whose value is supplied.

    Breakpoint order, widest first: desktop, tablet (<=1024),
    mobile_extra / "Mobile Landscape" (<=880), mobile (<=767).
    """
    out = {key: d}
    if t is not None: out[key + "_tablet"] = t
    if me is not None: out[key + "_mobile_extra"] = me
    if m is not None: out[key + "_mobile"] = m
    return out

def typo(family="Montserrat", size=None, size_t=None, size_m=None, weight="400",
         lh=None, lh_t=None, lh_m=None, ls=None, transform=None, prefix=""):
    """Style-tab typography. prefix e.g. 'title_' / 'description_' for image-box."""
    s = {prefix + "typography_typography": "custom",
         prefix + "typography_font_family": family,
         prefix + "typography_font_weight": weight}
    if size is not None:
        s.update(responsive(prefix + "typography_font_size",
                            px(size), px(size_t) if size_t else None,
                            px(size_m) if size_m else None))
    if lh is not None:
        s.update(responsive(prefix + "typography_line_height",
                            px(lh, "em"), px(lh_t, "em") if lh_t else None,
                            px(lh_m, "em") if lh_m else None))
    if ls is not None:
        s[prefix + "typography_letter_spacing"] = px(ls)
    if transform:
        s[prefix + "typography_text_transform"] = transform
    return s

def media(filename, alt=""):
    """Look up an imported attachment; fall back to a predictable URL + id 0."""
    m = _MEDIA.get(filename)
    if m:
        return {"url": m["url"], "id": m["id"], "alt": m.get("alt", alt), "source": "library"}
    return {"url": MEDIA_BASE + filename, "id": 0, "alt": alt, "source": "library"}

def link(url, external=False):
    return {"url": url, "is_external": "on" if external else "",
            "nofollow": "", "custom_attributes": "", "_id": eid("lnk")}

# ---------------------------------------------------------------- node helpers
def container(children, seed="c", inner=False, **settings):
    base = {"content_width": "boxed", "flex_direction": "column"}
    base.update(settings)
    return {"id": eid(seed), "elType": "container", "isInner": inner,
            "settings": base, "elements": children}

def widget(wtype, settings, seed=None):
    return {"id": eid(seed or wtype), "elType": "widget", "widgetType": wtype,
            "settings": settings, "elements": []}

# ---------------------------------------------------------------- design tokens
PRIMARY = "#053480"
NAVY    = "#0A1551"
SURFACE = "#F2F2F2"
TEXT    = "#000000"
WHITE   = "#FFFFFF"
MUTED   = "#6C73A8"
FONT    = "Montserrat"
MAXW    = 1320

def boxed(**kw):
    s = {"content_width": "boxed", "boxed_width": px(MAXW)}
    s.update(kw)
    return s

# ---------------------------------------------------------------- widget builders
def wwidth(size, size_t=None, size_m=None, unit="px"):
    """Widget-level width (Advanced > Layout > Width: Custom)."""
    s = {"_element_width": "initial"}
    s.update(responsive("_element_custom_width",
                        px(size, unit),
                        px(size_t, unit) if size_t is not None else None,
                        px(size_m, unit) if size_m is not None else None))
    return s

def heading(text, tag="h2", color=PRIMARY, align="center", size=(69, 54, 48),
            weight="600", lh=1.4, ls=-2.0, maxw=None, seed="h"):
    s = {"title": text, "header_size": tag, "title_color": color}
    s.update(responsive("align", align))
    s.update(typo(FONT, size[0], size[1], size[2], weight, lh, ls=ls))
    if maxw:
        s["_element_width"] = "initial"
        s["_element_custom_width"] = px(maxw)
        s["_element_custom_width_tablet"] = px(min(maxw, 640))
        s["_element_custom_width_mobile"] = px(100, "%")
    return widget("heading", s, seed)

def text(html, color=TEXT, align="left", size=(24, 22, 20), lh=1.4, weight="400", seed="t"):
    s = {"editor": html, "text_color": color}
    s.update(responsive("align", align))
    s.update(typo(FONT, size[0], size[1], size[2], weight, lh))
    return widget("text-editor", s, seed)

def button(label, url, style="primary", align="center", size=(25.6, 23.1, 21.4),
           full_mobile=False, weight="600", seed="btn"):
    s = {"text": label, "link": link(url), "size": "md", "button_type": ""}
    s.update(responsive("align", align, align, "justify" if full_mobile else align))
    s.update(typo(FONT, size[0], size[1], size[2], weight, 1.0, ls=-0.7))
    s.update(responsive("border_radius",
                        {"unit": "px", "top": "300", "right": "300", "bottom": "300", "left": "300", "isLinked": True}))
    s.update(pad((27, 38, 27, 38), (24, 36, 24, 36), (20, 24, 20, 24)))
    s["text_padding"] = s.pop("padding")
    s["text_padding_tablet"] = s.pop("padding_tablet")
    s["text_padding_mobile"] = s.pop("padding_mobile")
    if style == "primary":
        s.update({"background_color": PRIMARY, "button_text_color": SURFACE,
                  "button_background_hover_color": NAVY, "hover_color": SURFACE})
    elif style == "ghost":
        s.update({"background_color": "#00000000", "button_text_color": PRIMARY,
                  "border_border": "solid", "border_width": {"unit": "px", "top": "2", "right": "2",
                                                             "bottom": "2", "left": "2", "isLinked": True},
                  "border_color": PRIMARY,
                  "button_background_hover_color": PRIMARY, "hover_color": SURFACE,
                  "button_hover_border_color": PRIMARY})
    return widget("button", s, seed)

def image(filename, alt="", width=None, width_t=None, width_m=None, align="center",
          size="full", seed="img"):
    s = {"image": media(filename, alt), "image_size": size, "caption_source": "none"}
    s.update(responsive("align", align))
    if width:
        s.update(responsive("width", px(width),
                            px(width_t) if width_t else None,
                            px(width_m) if width_m else None))
    return widget("image", s, seed)

def image_box(filename, alt, title, body, title_tag="h3", align="center", img_w=128,
              img_w_t=124, img_w_m=179, seed="ib"):
    s = {"image": media(filename, alt), "thumbnail_size": "full",
         "title_text": title, "description_text": body,
         "title_size": title_tag, "position": "top",
         "title_color": PRIMARY, "description_color": TEXT,
         "image_space": px(24), "title_bottom_space": px(12)}
    s.update(responsive("text_align", align))
    # image-box sizes its image as a % of the box, so convert the target px
    # widths against the card width at each breakpoint (300 / 300 / 350).
    s.update(responsive("image_size", px(78, "%"), px(72, "%"), px(55, "%")))
    # the card itself: 4-up desktop, 2-up tablet, 1-up mobile
    s["_element_width"] = "initial"
    s.update(responsive("_element_custom_width",
                        px(23, "%"), px(46, "%"), px(100, "%")))
    s.update({"_padding": {"unit": "px", "top": "0", "right": "68",
                           "bottom": "0", "left": "68", "isLinked": False},
              "_padding_tablet": {"unit": "px", "top": "0", "right": "40",
                                  "bottom": "0", "left": "40", "isLinked": False},
              "_padding_mobile": {"unit": "px", "top": "0", "right": "16",
                                  "bottom": "0", "left": "16", "isLinked": False}})
    s.update(typo(FONT, 24, 24, 24, "600", 1.23, ls=-0.72, prefix="title_"))
    s.update(typo(FONT, 20.5, 19.5, 18, "400", 1.4, prefix="description_"))
    return widget("image-box", s, seed)

def icon_list(items, color=PRIMARY, size=24, seed="il"):
    return widget("icon-list", {
        "icon_list": [{"text": t, "link": link(u),
                       "selected_icon": {"value": "", "library": ""},
                       "_id": eid("ili")} for t, u in items],
        "space_between": px(6), "text_color": color, "icon_color": color,
        **typo(FONT, size, size - 2, size - 4, "400", 1.4)
    }, seed)


# ---------------------------------------------------------------- responsive fix-ups
def stack_overflowing_tablet_rows(node):
    """Make a row stack at tablet when its columns are 100% wide there.

    `col(w=60, w_t=100)` reads as "full width at tablet", but that only happens
    if the parent row also stacks — otherwise flex shrinks both children to 50%
    and you get two half-width columns on iPad instead of one full-width one.
    That is what made the hero, the proof block and the service body columns
    look cramped at 768-1024. Only tablet is touched; mobile is left exactly as
    authored.
    """
    if isinstance(node, list):
        for n in node:
            stack_overflowing_tablet_rows(n)
        return node
    s = node.get("settings", {})
    if node.get("elType") == "container":
        direction = s.get("flex_direction_tablet", s.get("flex_direction"))
        wraps = s.get("flex_wrap") == "wrap" or s.get("flex_wrap_tablet") == "wrap"
        if direction == "row" and not wraps:
            total, seen = 0.0, 0
            for c in node.get("elements", []):
                if c.get("elType") != "container":
                    seen = 0
                    break
                cs = c.get("settings", {})
                if cs.get("hide_tablet") == "hidden-tablet":
                    continue
                w = cs.get("width_tablet", cs.get("width"))
                if not (isinstance(w, dict) and w.get("unit") == "%"):
                    seen = 0
                    break
                total += float(w.get("size") or 0)
                seen += 1
            if seen >= 2 and total > 100.5:
                s["flex_direction_tablet"] = "column"
                s.setdefault("flex_align_items_tablet", "stretch")
    for c in node.get("elements", []):
        stack_overflowing_tablet_rows(c)
    return node


# ---------------------------------------------------------------- page sections
def s1_hero():
    return container([
        heading("Expert whole of market mortgage advice for landlords and homeowners",
                tag="h1", color=WHITE, align="left",
                size=(58, 46, 42), lh=1.27, ls=-1.75, maxw=500, seed="hero-h1"),
        button("Contact The Expert Broker", "/contact", "primary", align="left",
               full_mobile=True, seed="hero-btn"),
    ], seed="s1", **boxed(
        flex_direction="column",
        flex_justify_content="flex-end",
        **responsive("flex_align_items", "flex-start"),
        **gap(32, 28, 24),
        **responsive("min_height", px(1263), px(1078), px(865)),
        **pad((206, 0, 64, 0), (170, 0, 56, 0), (138, 20, 48, 20)),
        background_background="video",
        background_video_link="",                        # client MP4 — see spec
        background_video_fallback=media("hero-london-skyline.webp",
                                        "London skyline at sunset — The Expert Broker"),
        background_play_on_mobile="",
        background_overlay_background="gradient",
        background_overlay_color="#00000099",
        background_overlay_color_b="#00000000",
        background_overlay_gradient_type="linear",
        background_overlay_gradient_angle=px(0, "deg"),
        background_overlay_color_b_stop=px(60, "%"),
    ))

def s2_about():
    cards = [
        ("about-icon-1.webp", "A purple abstract logo combining a house and bar chart",
         "Over 20 years industry experience.", "Trusted implicitly by our clients."),
        ("about-icon-2.webp", "A blue abstract logo combining a house and bar chart",
         "From complex, niche limited company buy to lets to more typical residential transactions.",
         "We can lend our expertise to any scenario."),
        ("about-icon-3.webp", "Graphic combining a house outline and bar chart",
         "Flexible consultations to work around your schedule.",
         "We are happy to discuss your options at any time that suits you."),
        ("about-icon-4.webp", "Symbol combining a house outline and a bar chart",
         "Bespoke finance solutions tailored to your needs.",
         "…because no two clients are the same."),
    ]
    row = container([image_box(f, a, t, b, seed="about-card") for f, a, t, b in cards],
                    seed="s2-row", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "column"),
        flex_wrap="wrap",
        **responsive("flex_align_items", "flex-start"),
        flex_justify_content="center",
        **gap(24, 20, 24),
    ))
    return container([
        heading("About Us", seed="s2-h2"),
        row,
        button("Discover More", "/about", "ghost", seed="s2-btn"),
    ], seed="s2", **boxed(
        flex_direction="column",
        **responsive("flex_align_items", "center"),
        **gap(48, 40, 32),
        **pad((120, 0, 118, 0), (86, 0, 84, 0), (56, 20, 40, 20)),
        background_background="classic", background_color=SURFACE,
    ))

def s3_band():
    return container([], seed="s3", **dict(
        content_width="full",
        **responsive("min_height", px(549), px(425), px(82)),
        **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        background_background="classic",
        background_image=media("band-london-terraces.webp", ""),
        background_size="cover", background_position="center center",
        background_repeat="no-repeat",
        shape_divider_top="tilt", shape_divider_top_color=SURFACE,
        **responsive("shape_divider_top_height", px(78), px(60), px(24)),
        shape_divider_bottom="tilt", shape_divider_bottom_color=SURFACE,
        shape_divider_bottom_flip="yes",
        **responsive("shape_divider_bottom_height", px(78), px(60), px(24)),
    ))

SERVICES = [
    ("service-buy-to-let.webp", "A miniature model of a house with a set of house keys",
     "Buy to Let", "Helping landlords maximise profits by securing competitive rates.",
     "/buy-to-let"),
    ("service-residential.webp", "An aerial view of a residential neighbourhood",
     "Residential", "First time Buyer or need to remortgage? We have access to whole of market rates.",
     "/residential"),
    ("service-limited-company-buy-to-let.webp", "A person holding a keyring with house-shaped keys",
     "Limited Company Buy to Let",
     "Mortgage solutions for landlords with properties held within a limited company.",
     "/limited-company-buy-to-let"),
    ("service-hmo.webp", "Modern building with reflective glass windows",
     "HMO's", "Specialist student and professional HMO mortgages.", "/hmos"),
    ("service-multi-unit-mufb.webp", "Looking up at four tall buildings",
     "Multi-unit (MUFB)", "Specialist finance for multiple flats under one freehold title.",
     "/multi-unit-mufb"),
    ("service-commercial-semi-commercial.webp", "Tall modern skyscrapers in an urban cityscape",
     "Commercial and Semi-commercial",
     "Assisting landlords who are looking to purchase/remortgage business premises office blocks, "
     "retail units and a wide array of commercial assets.",
     "/commercial-and-semi-commercial"),
    ("service-bridging-finance.webp", "A hand holding a key near a calculator on a desk",
     "Bridging Finance", "Short term finance solutions for renovation projects or auction purchases.",
     "/bridging-finance"),
]

def service_card(f, alt, title, body, url):
    return container([
        image(f, alt, width=459, width_t=316, width_m=269, align="left",
              size="large", seed="svc-img"),
        heading(title, tag="h3", align="left", size=(24, 24, 24), lh=1.23,
                ls=-0.72, seed="svc-h3"),
        text(f"<p>{body}</p>", align="left", size=(24, 22, 20), seed="svc-txt"),
        button("Read More", url, "primary", align="left",
               size=(18.7, 18.2, 17), seed="svc-btn"),
    ], seed="svc-card", inner=True, **dict(
        content_width="full",
        flex_direction="column",
        **responsive("flex_align_items", "flex-start"),
        **gap(28, 24, 20),
        **responsive("width", px(48, "%"), px(48, "%"), px(100, "%")),
    ))

def s4_services():
    cards = [service_card(*s) for s in SERVICES]
    cards.append(container([
        image("services-secondary-graphic.webp", "The Expert Broker",
              width=300, width_t=240, width_m=220, align="left", seed="svc-cta-logo"),
        text("<p>Contact us for expert whole of market mortgage advice for landlords "
             "and homeowners.</p>", align="left", size=(24, 22, 20), seed="svc-cta-txt"),
        button("Contact The Expert Broker", "/contact", "primary", align="left",
               size=(18.7, 18.2, 17), seed="svc-cta-btn"),
    ], seed="svc-cta", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"),
        **gap(20, 18, 16),
        **responsive("width", px(48, "%"), px(48, "%"), px(100, "%")),
    )))
    row = container(cards, seed="s4-row", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "column"),
        flex_wrap="wrap",
        **responsive("flex_align_items", "flex-start"),
        flex_justify_content="space-between",
        flex_gap={"unit": "px", "size": 40, "column": "40", "row": "170", "isLinked": False},
        flex_gap_tablet={"unit": "px", "size": 32, "column": "32", "row": "120", "isLinked": False},
        flex_gap_mobile={"unit": "px", "size": 40, "column": "40", "row": "72", "isLinked": False},
    ))
    return container([heading("Services", seed="s4-h2"), row], seed="s4", **boxed(
        flex_direction="column",
        **responsive("flex_align_items", "center"),
        **gap(48, 40, 32),
        **pad((96, 0, 86, 0), (68, 0, 61, 0), (48, 20, 24, 20)),
        background_background="classic", background_color=SURFACE,
    ))

STEPS = [
    ("step-1.webp", "The Expert Broker step one logo", "An initial discussion",
     "We will have a detailed discussion regarding your plans to purchase or remortgage a "
     "property. This is an opportunity for us to dispense any initial advice in respect of how "
     "to structure the transaction, and to obtain all pertinent information that will help us "
     "provide with you an accurate quotation."),
    ("step-2.webp", "The Expert Broker step two logo", "Recommendation",
     "You will then receive a personalised, tailored recommendation specific to your needs. Our "
     "recommendations always come with a comprehensive and transparent analysis of the lender "
     "and product(s) selected."),
    ("step-3.webp", "The Expert Broker step three logo", "Secure your mortgage offer",
     "We will liaise with the lenders underwriters to obtain your formal mortgage offer which "
     "will be then be sent to your solicitors to carry out the necessary conveyancing to allow "
     "you to complete on the mortgage."),
]

def step_col(f, alt, title, body):
    return container([
        image(f, alt, width=100, width_t=90, width_m=80, align="left", seed="step-img"),
        heading(title, tag="h3", color=SURFACE, align="left",
                size=(27, 24, 22), lh=1.4, ls=0, seed="step-h3"),
        text(f"<p>{body}</p>", color=SURFACE, align="left",
             size=(20.5, 19.5, 18), seed="step-txt"),
    ], seed="step-col", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"),
        **gap(38, 30, 20),
        **responsive("width", px(340), px(260), px(100, "%")),
    ))

def step_arrow():
    return widget("icon", {
        "selected_icon": {"value": "fas fa-arrow-right", "library": "fa-solid"},
        "view": "default", "primary_color": SURFACE,
        **responsive("size", px(34), px(28), px(22)),
        **responsive("align", "center"),
        "_element_width": "initial",
        **responsive("_element_custom_width", px(60), px(48), px(100, "%")),
        **responsive("_element_custom_width_mobile", px(100, "%")),
        "_margin": {"unit": "px", "top": "40", "right": "0",
                    "bottom": "0", "left": "0", "isLinked": False},
    }, "step-arrow")

def s5_steps():
    cols = []
    steps = [step_col(*s) for s in STEPS]
    for i, c in enumerate(steps):
        cols.append(c)
        if i < len(steps) - 1:
            cols.append(step_arrow())
    row = container(cols, seed="s5-row", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "column"),
        **responsive("flex_align_items", "flex-start"),
        flex_justify_content="space-between",
        **gap(30, 24, 32),
    ))
    return container([heading("Step by Step Guide", color=SURFACE, seed="s5-h2"), row],
                     seed="s5", **dict(
        content_width="boxed", boxed_width=px(1226),
        boxed_width_tablet=px(940), boxed_width_mobile=px(350),
        flex_direction="column",
        **responsive("flex_align_items", "center"),
        **gap(48, 40, 32),
        **pad((130, 0, 190, 0), (96, 0, 140, 0), (70, 20, 96, 20)),
        background_background="classic", background_color=PRIMARY,
        shape_divider_top="triangle", shape_divider_top_color=SURFACE,
        **responsive("shape_divider_top_height", px(62), px(48), px(30)),
        shape_divider_bottom="triangle", shape_divider_bottom_color=SURFACE,
        shape_divider_bottom_flip="yes",
        **responsive("shape_divider_bottom_height", px(62), px(48), px(30)),
    ))

# Review text: only the four visible cards were captured verbatim. The remaining
# seven reviewers are known by name; their text must be supplied before push.
REVIEWS = [
    ("Millie", "3 months ago",
     "Excellent service from start to finish. They were friendly, knowledgeable, and always "
     "available to answer any questions. They made the whole process straightforward."),
    ("mark wilson", "2 months ago",
     "Steve has looked after my Portfolio for years, has saved me tens of thousands of pounds "
     "over the years. A lovely guy and more."),
    ("F Hussain", "3 months ago",
     "As a Portfolio landlord, I've used Steve for many years and found him to be very "
     "knowledgeable and trustworthy. My daughter is also a client now."),
    ("Becky M", "3 months ago",
     "Fantastic mortgage broker. Great communication, expert advice, and a smooth process "
     "throughout. Highly recommended."),
    # NEEDS COPY: Koren Hornby, Rebecca Farrell, Rosie Moss, Amy-H W,
    #             jacqueline gibney, S C, Shell Curtin
]

def stars(size=13, color="#FBBC04", seed="stars"):
    return widget("star-rating", {
        "rating": 5, "star_style": "star_unicode", "unmarked_star_style": "solid",
        "stars_color": color, "unmarked_star_color": "#E0E0E0",
        **responsive("icon_size", px(size)),
        "star_space": px(2),
        **responsive("align", "left"),
        "title": "",
    }, seed)


def avatar(letter, colour, seed="avatar"):
    """The reference uses Google's coloured letter avatars."""
    return container([
        heading(letter, tag="div", color=WHITE, align="center",
                size=(20, 20, 20), lh=1.0, ls=0, seed="avatar-l"),
    ], seed=seed, inner=True, **dict(
        content_width="full", flex_direction="column",
        flex_justify_content="center",
        **responsive("flex_align_items", "center"),
        **gap(0, 0, 0), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        **responsive("width", px(51), px(48), px(46)),
        **responsive("min_height", px(51), px(48), px(46)),
        background_background="classic", background_color=colour,
        border_radius={"unit": "px", "top": "300", "right": "300",
                       "bottom": "300", "left": "300", "isLinked": True},
    ))


# name, when, colour of the letter avatar, review text
REVIEWS = [
    ("mark wilson", "2 months ago", "#1A73E8",
     "Steve has looked after my Portfolio for years, has saved me tens of thousands of "
     "pounds over the years. A lovely guy and more..."),
    ("F Hussain", "3 months ago", "#4285F4",
     "As a Portfolio landlord, I've used Steve for many years and found him to be very "
     "knowledgeable and trustworthy. My daughter is a..."),
    ("Becky M", "3 months ago", "#5F6368",
     "Fantastic mortgage broker. Great communication, expert advice, and a smooth process "
     "throughout. Highly recommended. Looking..."),
    ("Koren Hornby", "2 months ago", "#E8710A",
     "I wouldn't trust anybody else with my mortgages. Extremely knowledgeable."),
    # NEEDS COPY: Millie, Rebecca Farrell, Rosie Moss, Amy-H W,
    #             jacqueline gibney, S C, Shell Curtin
]


def review_card(name, when, colour, body):
    who = container([
        avatar(name[0].upper(), colour, seed="rv-av"),
        container([
            heading(name, tag="div", color=NAVY, align="left",
                    size=(17, 17, 16), lh=1.3, ls=0, seed="rv-name"),
            text(f"<p>{when}</p>", color=MUTED, align="left",
                 size=(13.8, 13.8, 13), lh=1.3, seed="rv-when"),
        ], seed="rv-who-t", inner=True, **dict(
            content_width="full", flex_direction="column",
            **responsive("flex_align_items", "flex-start"),
            **gap(2, 2, 2), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        )),
    ], seed="rv-who", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "row"),
        **responsive("flex_align_items", "center"),
        **gap(12, 12, 12), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
    ))
    return container([
        stars(seed="rv-stars"),
        text(f'<p>{body}</p><p><a href="https://search.google.com/local/reviews" '
             f'target="_blank" rel="noopener">Read more</a></p>', color=NAVY,
             align="left", size=(14.9, 14.9, 14), lh=1.45, seed="rv-body"),
        who,
    ], seed="rv-card", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"),
        flex_justify_content="space-between",
        **gap(14, 12, 12),
        **pad((20, 20, 20, 20), (18, 18, 18, 18), (18, 18, 18, 18)),
        **responsive("width", px(23, "%"), px(47, "%"), px(100, "%")),
        background_background="classic", background_color=WHITE,
        border_radius={"unit": "px", "top": "8", "right": "8",
                       "bottom": "8", "left": "8", "isLinked": True},
        box_shadow_box_shadow_type="yes",
        box_shadow_box_shadow={"horizontal": 0, "vertical": 2, "blur": 10,
                               "spread": 0, "color": "rgba(0,0,0,0.08)"},
    ))


def s6_reviews():
    """Heading only — the review content is handled by a reviews plugin.
    The empty container below is the drop target for the plugin's widget."""
    slot = container([], seed="s6-slot", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "stretch"),
        **gap(0, 0, 0), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        **responsive("min_height", px(430), px(430), px(560)),
    ))
    return container([
        heading("Our Happy Clients!", color="#8A93B8", seed="s6-h2"),
        slot,
    ], seed="s6", **boxed(
        flex_direction="column",
        **responsive("flex_align_items", "stretch"),
        **gap(24, 20, 18),
        **pad((70, 0, 70, 0), (56, 0, 56, 0), (40, 20, 40, 20)),
        background_background="classic", background_color=SURFACE,
    ))


LENDERS = ["bm-solutions", "paragon", "santander", "the-mortgage-works", "barclays",
           "fleet-mortgages", "godiva", "hsbc", "hampshire-trust-bank", "interbay",
           "natwest", "precise", "shawbrook"]
LENDER_NAMES = {"bm-solutions": "BM Solutions", "paragon": "Paragon", "santander": "Santander",
                "the-mortgage-works": "The Mortgage Works", "barclays": "Barclays",
                "fleet-mortgages": "Fleet Mortgages", "godiva": "Godiva", "hsbc": "HSBC",
                "hampshire-trust-bank": "Hampshire Trust Bank", "interbay": "InterBay",
                "natwest": "NatWest", "precise": "Precise.", "shawbrook": "Shawbrook"}

def s7_lenders():
    """All 13 lenders in one wrapping grid — no carousel, no navigation."""
    logos = []
    for k in LENDERS:
        w = image(f"lender-{k}.webp", LENDER_NAMES[k],
                  width=150, width_t=132, width_m=118, align="center",
                  seed=f"lender-{k}")
        w["settings"]["_element_width"] = "initial"
        w["settings"].update(responsive("_element_custom_width",
                                        px(150), px(132), px(118)))
        logos.append(w)
    grid = container(logos, seed="s7-grid", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "row"),
        flex_wrap="wrap",
        **responsive("flex_align_items", "center"),
        flex_justify_content="center",
        flex_gap={"unit": "px", "size": 38, "column": "38", "row": "48", "isLinked": False},
        flex_gap_tablet={"unit": "px", "size": 48, "column": "48", "row": "36", "isLinked": False},
        flex_gap_mobile={"unit": "px", "size": 28, "column": "28", "row": "28", "isLinked": False},
    ))
    return container([heading("Mortgage Lenders", seed="s7-h2"), grid],
                     seed="s7", **boxed(
        flex_direction="column",
        **responsive("flex_align_items", "center"),
        **gap(48, 40, 32),
        **pad((72, 0, 72, 0), (56, 0, 56, 0), (40, 20, 40, 20)),
        background_background="classic", background_color=SURFACE,
    ))


SERVICE_LINKS = [("Buy to Let", "/buy-to-let"), ("Residential", "/residential"),
                 ("Limited Company Buy to Let", "/limited-company-buy-to-let"),
                 ("HMO's", "/hmos"), ("Multi-unit (MUFB)", "/multi-unit-mufb"),
                 ("Commercial & Semi-commercial", "/commercial-and-semi-commercial"),
                 ("Bridging Finance", "/bridging-finance")]
COMPANY_LINKS = [("About Us", "/about"), ("Contact Us", "/contact"), ("FAQs", "/faqs"),
                 ("Case Studies", "/case-studies"), ("Reviews", "/reviews"),
                 ("Privacy Notice", "/privacy-notice"),
                 ("Complaints Procedure", "/complaints-procedure")]

LEGAL = [
    "Your property may be repossessed if you do not keep up repayments on your mortgage.",
    "The guidance and/or information contained within this site is subject to the UK regulatory "
    "regime and is therefore targeted at consumers based in the UK.",
    "Your initial mortgage consultation is free of charge and without obligation. We normally "
    "charge a fee for our mortgage service, however, this will depend on your circumstances and "
    "the complexity of the deal. Our standard fee for mortgages is £595. Our standard fee for "
    "bridging applications is £995. Our standard fee for commercial mortgages is £995. All our "
    "fees are only payable on receipt of your offer, and we will discuss and agree on the fee "
    "with you before submitting any mortgage application.",
    "The FCA do not regulate some forms of Business Buy to Let Mortgages and Commercial "
    "Mortgages to Ltd Companies.",
    "The Expert Broker Ltd is registered in England and Wales. No. 17105788. Registered Office: "
    "300 St. Marys Road, Garston, Liverpool, L19 0NQ.",
    "The Expert Broker Ltd is an Appointed Representative of Cornerstone Finance Group Ltd, "
    "which is authorised and regulated by the Financial Conduct Authority.",
    "Cornerstone Finance Group Ltd is registered in England &amp; Wales. No. 08458702. "
    "Registered Office: Unit E Copse Walk, Pontprennau, Cardiff, CF23 8RB.",
    "The Expert Broker Ltd (No. 1055324) and Cornerstone Finance Group Ltd (No. 767202) are "
    "entered on the Financial Services Register at "
    "<a href=\"https://register.fca.org.uk/\" target=\"_blank\" rel=\"noopener\">"
    "https://register.fca.org.uk/</a>.",
]

def s8_contact():
    col1 = container([
        image("the-expert-broker-logo.webp", "The Expert Broker", width=320,
              width_t=280, width_m=240, align="left", seed="foot-logo"),
        widget("social-icons", {
            "social_icon_list": [
                {"social_icon": {"value": "fab fa-instagram", "library": "fa-brands"},
                 "link": link("https://www.instagram.com/", True), "_id": eid("soc")},
                {"social_icon": {"value": "fab fa-linkedin-in", "library": "fa-brands"},
                 "link": link("https://www.linkedin.com/", True), "_id": eid("soc")},
            ],
            "shape": "circle", "align": "left",
            "icon_primary_color": PRIMARY, "icon_secondary_color": SURFACE,
        }, "social"),
        button("Contact Us", "/contact", "primary", align="left",
               full_mobile=True, seed="foot-btn"),
    ], seed="foot-c1", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"), **gap(24, 20, 20),
        **responsive("width", px(30, "%"), px(30, "%"), px(100, "%")),
    ))
    col2 = container([
        heading("Services", tag="h3", align="left", size=(24, 24, 24), lh=1.23,
                ls=-0.72, seed="foot-h3a"),
        icon_list(SERVICE_LINKS, seed="foot-l1"),
        icon_list(COMPANY_LINKS, seed="foot-l2"),
    ], seed="foot-c2", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"), **gap(24, 20, 20),
        **responsive("width", px(28, "%"), px(28, "%"), px(100, "%")),
    ))
    col3 = container([
        heading("Important Information", tag="h3", align="left", size=(24, 24, 24),
                lh=1.23, ls=-0.72, seed="foot-h3b"),
        text("".join(f"<p>{p}</p>" for p in LEGAL), align="left",
             size=(20.5, 19.5, 18), seed="foot-legal"),
    ], seed="foot-c3", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"), **gap(16, 14, 14),
        **responsive("width", px(38, "%"), px(38, "%"), px(100, "%")),
    ))
    row = container([col1, col2, col3], seed="foot-row", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "column"),
        **responsive("flex_align_items", "flex-start"),
        flex_justify_content="space-between",
        **gap(48, 40, 40),
    ))
    return container([row], seed="s8", **boxed(
        flex_direction="column",
        **pad((96, 0, 64, 0), (68, 0, 48, 0), (48, 20, 40, 20)),
        background_background="classic", background_color=SURFACE,
    ))

# ---------------------------------------------------------------- header
MENU_SLUG = "primary"

def build_header():
    """Transparent header overlaying the hero, as the reference does:
    absolute position, 206px tall, logo left, nav + pill CTA right."""
    logo = container([
        image("header-logo.webp", "The Expert Broker", width=259, width_t=220,
              width_m=150, align="left", seed="hdr-logo"),
    ], seed="hdr-c1", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-start"),
        **gap(0, 0, 0), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        **responsive("width", px(28, "%"), px(30, "%"), px(55, "%")),
    ))
    nav = widget("nav-menu", {
        "menu": MENU_SLUG,
        "layout": "horizontal",
        **responsive("align", "center"),
        "submenu_icon": {"value": "fas fa-caret-down", "library": "fa-solid"},
        "pointer": "none",
        "color_menu_item": PRIMARY,
        "color_menu_item_hover": NAVY,
        "color_menu_item_active": NAVY,
        **typo(FONT, 23.9, 21.9, 20.3, "600", 1.6, ls=-0.7, prefix="menu_"),
        # mobile: burger, as the reference
        "dropdown": "tablet",
        "full_width": "stretch",
        "toggle": "burger",
        **responsive("toggle_size", px(30), px(30), px(28)),
        "toggle_color": PRIMARY,
        "toggle_background_color": "#00000000",
        "color_dropdown_item": PRIMARY,
        "background_color_dropdown_item": "#FFFFFF",
        "color_dropdown_item_hover": NAVY,
        **typo(FONT, 22, 22, 22, "600", 1.5, prefix="dropdown_"),
        "padding_horizontal_dropdown_item": px(24),
        "padding_vertical_dropdown_item": px(14),
        "dropdown_divider_width": px(0),
        "padding_horizontal_menu_item": px(14),
        "padding_vertical_menu_item": px(8),
    }, "hdr-nav")
    navcol = container([nav], seed="hdr-c2", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "center", "center", "flex-end"),
        **gap(0, 0, 0), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        **responsive("width", px(34, "%"), px(34, "%"), px(45, "%")),
    ))
    cta = container([
        button("Contact The Expert Broker", "/contact", "primary",
               align="right", weight="400", seed="hdr-btn"),
    ], seed="hdr-c3", inner=True, **dict(
        content_width="full", flex_direction="column",
        **responsive("flex_align_items", "flex-end"),
        **gap(0, 0, 0), **pad((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)),
        **responsive("width", px(38, "%"), px(36, "%"), px(1, "%")),
        hide_mobile="hidden-mobile",
    ))
    row = container([logo, navcol, cta], seed="hdr-row", inner=True, **dict(
        content_width="full",
        **responsive("flex_direction", "row", "row", "row"),
        flex_wrap="nowrap",
        **responsive("flex_align_items", "center"),
        flex_justify_content="space-between",
        **gap(24, 20, 8),
    ))
    return {
        "version": ELEMENTOR_VERSION, "title": "Header", "type": "header",
        "page_settings": {},
        "content": [container([row], seed="hdr", **boxed(
            flex_direction="column",
            **responsive("flex_align_items", "center"),
            **gap(0, 0, 0),
            **pad((44, 0, 44, 0), (36, 0, 36, 0), (20, 20, 20, 20)),
            **responsive("min_height", px(206), px(186), px(138)),
            background_background="classic",
            background_color="#00000000",
            position="absolute",
            _position="absolute",
            **responsive("_offset_orientation_h", "start"),
            z_index=99,
        ))],
    }


def build_footer():
    """The reference's footer, lifted out of the page into a Theme Builder
    template: logo + socials + CTA, two link lists, and the legal block."""
    doc = s8_contact()
    return {
        "version": ELEMENTOR_VERSION, "title": "Footer", "type": "footer",
        "page_settings": {},
        "content": [doc],
    }


# ---------------------------------------------------------------- page
def build_home():
    return {
        "version": ELEMENTOR_VERSION,
        "title": "Home",
        "type": "page",
        "page_settings": {
            "hide_title": "yes",
            "background_background": "classic",
            "background_color": SURFACE,
        },
        # S8 now lives in the Theme Builder footer template, not the page.
        "content": [
            s1_hero(), s2_about(), s3_band(), s4_services(),
            s5_steps(), s6_reviews(), s7_lenders(),
        ],
    }

PAGES = {"home": build_home, "header": build_header, "footer": build_footer}

if __name__ == "__main__":
    import sys
    wanted = sys.argv[1:] or list(PAGES)
    for name in wanted:
        doc = PAGES[name]()
        out = os.path.join(TEMPLATES, f"{name}.json")
        json.dump(doc, open(out, "w"), indent=1)
        ids = []
        def walk(n):
            ids.append(n["id"])
            for c in n.get("elements", []):
                walk(c)
        for c in doc["content"]:
            walk(c)
        assert len(ids) == len(set(ids)), "duplicate element ids"
        print(f"{name}.json  {len(doc['content'])} sections  {len(ids)} elements  "
              f"{os.path.getsize(out)} bytes")
