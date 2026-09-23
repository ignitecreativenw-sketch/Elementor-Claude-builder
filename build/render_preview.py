#!/usr/bin/env python3
"""
Render an Elementor container/widget JSON template to static HTML so a design
can be reviewed before anything is pushed to staging.

  python3 build/render_preview.py templates/about.json 1440 > qa/about-preview.html

It reads the same settings Elementor reads (flex direction, gaps, padding,
widths, typography, colours, radii, borders) and maps them onto plain flexbox,
so what you see is what the container stack will produce. Supported widgets:
heading, text-editor, image, button, star-rating, icon-list,
accordion, form, divider, html (deliberately blank) and the theme/post set.
"""
import json, os, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

BP = "desktop"    # set from argv: desktop | tablet | mobile_extra | mobile
SUF = {"desktop": "", "tablet": "_tablet",
       "mobile_extra": "_mobile_extra", "mobile": "_mobile"}


def g(s, key, default=None):
    """Responsive getter: fall back down the breakpoint chain like Elementor."""
    order = {"desktop": [""], "tablet": ["_tablet", ""],
             "mobile_extra": ["_mobile_extra", "_tablet", ""],
             "mobile": ["_mobile", "_mobile_extra", "_tablet", ""]}[BP]
    for suf in order:
        v = s.get(key + suf)
        if v not in (None, ""):
            return v
    return default


def unit(v, default=None):
    if not isinstance(v, dict):
        return default
    size = v.get("size")
    if size in (None, ""):
        return default
    return f"{size}{v.get('unit', 'px')}"


def box(v):
    if not isinstance(v, dict):
        return None
    u = v.get("unit", "px")
    return " ".join(f"{v.get(k, 0) or 0}{u}"
                    for k in ("top", "right", "bottom", "left"))


def typo_css(s, prefix=""):
    out = []
    p = prefix
    fam = g(s, p + "typography_font_family")
    if fam:
        out.append(f"font-family:'{fam}',system-ui,sans-serif")
    size = unit(g(s, p + "typography_font_size"))
    if size:
        out.append(f"font-size:{size}")
    w = g(s, p + "typography_font_weight")
    if w:
        out.append(f"font-weight:{w}")
    lh = unit(g(s, p + "typography_line_height"))
    if lh:
        out.append(f"line-height:{lh.replace('em','')}")
    ls = unit(g(s, p + "typography_letter_spacing"))
    if ls:
        out.append(f"letter-spacing:{ls}")
    return out


HIDE_KEY = {"desktop": "hide_desktop", "tablet": "hide_tablet",
            "mobile_extra": "hide_mobile_extra", "mobile": "hide_mobile"}


def hidden(s):
    """Elementor's Responsive > Visibility, at the breakpoint being rendered."""
    return bool(s.get(HIDE_KEY[BP]))


def common(s):
    """Element-level width / padding shared by widgets and containers."""
    out = []
    if hidden(s):
        out.append("display:none")
    if g(s, "_element_width") == "initial":
        w = unit(g(s, "_element_custom_width"))
        if w:
            out.append(f"width:{w}")
            out.append("flex:0 0 auto")
    p = box(g(s, "_padding"))
    if p:
        out.append(f"padding:{p}")
    # Containers that clip their children — the rounded card images and the
    # round portrait both rely on this, and without it every card in every
    # preview taken so far has shown square corners.
    ov = g(s, "overflow")
    if ov:
        out.append(f"overflow:{ov}")
    return out


IMG_ROOT = os.path.join(ROOT, "assets")


def img_src(m):
    url = m.get("url", "")
    name = url.rsplit("/", 1)[-1]
    local = os.path.join(IMG_ROOT, name)
    return local if os.path.exists(local) else url


def decor(s):
    out = []
    if s.get("background_background") == "classic":
        c = g(s, "background_color")
        img = g(s, "background_image")
        if isinstance(img, dict) and img.get("url"):
            # Elementor paints the overlay in a ::before above the image; a
            # static preview layers it as a gradient in front of the same
            # image so hero contrast can actually be judged here.
            layers = []
            if s.get("background_overlay_background") == "gradient":
                ang = unit(g(s, "background_overlay_gradient_angle"), "180deg")
                ca = g(s, "background_overlay_color", "#00000000")
                cb = g(s, "background_overlay_color_b", "#00000000")
                sa = unit(g(s, "background_overlay_color_stop"), "0%")
                sb = unit(g(s, "background_overlay_color_b_stop"), "100%")
                layers.append(f"linear-gradient({ang}, {ca} {sa}, {cb} {sb})")
            elif s.get("background_overlay_background") == "classic":
                co = g(s, "background_overlay_color")
                if co:
                    layers.append(f"linear-gradient({co}, {co})")
            layers.append(f"url('{img_src(img)}')")
            out.append("background-image:" + ",".join(layers))
            out.append(f"background-size:{g(s, 'background_size', 'cover')}")
            out.append(f"background-position:"
                       f"{g(s, 'background_position', 'center center')}")
            out.append("background-repeat:no-repeat")
            if c:
                out.append(f"background-color:{c}")
        elif c:
            out.append(f"background:{c}")
    if g(s, "border_border") == "solid":
        bw = g(s, "border_width")
        bc = g(s, "border_color", "#000")
        if isinstance(bw, dict):
            u = bw.get("unit", "px")
            for side in ("top", "right", "bottom", "left"):
                val = bw.get(side, 0) or 0
                if str(val) != "0":
                    out.append(f"border-{side}:{val}{u} solid {bc}")
    r = box(g(s, "border_radius"))
    if r:
        out.append(f"border-radius:{r}")
    return out


# ------------------------------------------------------------------ widgets
def w_heading(s):
    tag = s.get("header_size", "h2")
    css = typo_css(s) + [f"color:{g(s, 'title_color', '#000')}",
                         f"text-align:{g(s, 'align', 'left')}", "margin:0"]
    css += common(s)
    return f'<{tag} style="{";".join(css)}">{s.get("title","")}</{tag}>'


def w_text(s):
    css = typo_css(s) + [f"color:{g(s, 'text_color', '#000')}",
                         f"text-align:{g(s, 'align', 'left')}"]
    css += common(s)
    body = s.get("editor", "")
    return f'<div class="te" style="{";".join(css)}">{body}</div>'


def w_image(s):
    m = s.get("image", {})
    css = ["display:block", "max-width:100%", "height:auto"]
    w = unit(g(s, "width"))
    if w:
        css.append(f"width:{w}")
    r = box(g(s, "image_border_radius"))
    if r:
        css.append(f"border-radius:{r}")
    wrap = [f"text-align:{g(s, 'align', 'center')}"] + common(s)
    inner = "margin:0 auto" if g(s, "align", "center") == "center" else ""
    return (f'<div style="{";".join(wrap)}">'
            f'<img src="{img_src(m)}" alt="{html.escape(m.get("alt","") or "")}" '
            f'style="{";".join(css)};{inner}"></div>')


def w_button(s):
    css = typo_css(s) + [
        f"color:{g(s, 'button_text_color', '#fff')}",
        "display:inline-block", "text-decoration:none", "border:0",
    ]
    bg = g(s, "background_color")
    if bg and bg != "#00000000":
        css.append(f"background:{bg}")
    else:
        css.append("background:transparent")
    if g(s, "border_border") == "solid":
        bw = g(s, "border_width")
        u = (bw or {}).get("unit", "px")
        css.append(f"border:{(bw or {}).get('top', 2)}{u} solid "
                   f"{g(s, 'border_color', '#053480')}")
    r = box(g(s, "border_radius"))
    if r:
        css.append(f"border-radius:{r}")
    p = box(g(s, "text_padding"))
    if p:
        css.append(f"padding:{p}")
    align = g(s, "align", "center")
    outer = [f"text-align:{'left' if align == 'left' else align}"] + common(s)
    if align == "justify":
        css.append("display:block")
    return (f'<div style="{";".join(outer)}">'
            f'<a style="{";".join(css)}">{s.get("text","")}</a></div>')


def w_stars(s):
    size = unit(g(s, "icon_size"), "16px")
    c = g(s, "stars_color", "#E8B93F")
    return (f'<div style="color:{c};font-size:{size};letter-spacing:2px">'
            f'&#9733;&#9733;&#9733;&#9733;&#9733;</div>')


def w_icon_list(s):
    css = typo_css(s) + [f"color:{g(s, 'text_color', '#000')}",
                         "margin:0", "padding:0", "list-style:none"]
    ic = g(s, "icon_color", "#053480")
    items = "".join(
        f'<li style="display:flex;gap:8px;align-items:flex-start">'
        f'<span style="color:{ic};flex:0 0 auto">&#10003;</span>'
        f'<span>{i.get("text","")}</span></li>'
        for i in s.get("icon_list", []))
    return f'<ul style="{";".join(css)}">{items}</ul>'


# ------------------------------------------------- dynamic widgets (stubs)
# The Posts and theme-post-* widgets pull from WordPress at render time, so a
# static preview has to stand in for them. qa/preview-posts.json holds the
# sample posts; the markup below mirrors what Elementor's Classic skin and the
# theme-post widgets output, so the preview is representative rather than
# pixel-exact. It exists to judge layout, not to replace looking at the site.
def _posts_data():
    path = os.path.join(ROOT, "qa", "preview-posts.json")
    try:
        return json.load(open(path))
    except Exception:
        return []


def _css(s, prefix, fallback):
    css = typo_css(s, prefix)
    return ";".join(css) if css else fallback


def w_posts(s):
    data = _posts_data()
    offset = int(s.get("posts_offset") or s.get("offset") or 0)
    per = int(s.get("posts_per_page") or 3)
    cols = int(g(s, "columns", "3"))
    items = data[offset:offset + per]
    if not items:
        msg = s.get("nothing_found_message", "")
        return (f'<div style="color:{BODY_C};font-size:16px;padding:8px 0">'
                f'{msg}</div>') if msg else ""
    gap_px = (s.get("item_gap") or {}).get("size", 28)
    cards = []
    for p in items:
        pad = box(s.get("box_content_padding")) or "26px"
        cards.append(
            f'<article style="flex:1 1 0;min-width:0;background:'
            f'{s.get("box_bg_color", "#fff")};border:1px solid '
            f'{s.get("box_border_color", "#E3E6EF")};border-radius:'
            f'{(s.get("box_border_radius") or {}).get("size", 14)}px;'
            f'overflow:hidden;display:flex;flex-direction:column">'
            f'<img src="{os.path.join(IMG_ROOT, p["image"])}" alt="" '
            f'style="width:100%;height:{220 if cols == 1 else 190}px;'
            f'object-fit:cover;display:block">'
            f'<div style="padding:{pad};display:flex;flex-direction:column;'
            f'gap:10px">'
            f'<div style="{_css(s, "meta_typography_", "font-size:13px")};'
            f'color:{s.get("meta_color", "#5A6480")}">{p["date"]}</div>'
            f'<h3 style="{_css(s, "title_typography_", "font-size:20px")};'
            f'color:{s.get("title_color", "#0A1551")};margin:0">'
            f'{p["title"]}</h3>'
            f'<p style="{_css(s, "excerpt_typography_", "font-size:15px")};'
            f'color:{s.get("excerpt_color", "#4A5378")};margin:0">'
            f'{p["excerpt"]}</p>'
            f'<span style="{_css(s, "read_more_typography_", "font-size:15px")};'
            f'color:{s.get("read_more_color", "#053480")}">'
            f'{s.get("classic_read_more_text", "Read more")}</span>'
            f'</div></article>')
    return (f'<div style="display:flex;flex-wrap:wrap;gap:{gap_px}px;'
            f'align-items:stretch">{"".join(cards)}</div>')


def w_post_title(s):
    p = (_posts_data() or [{}])[0]
    css = typo_css(s) + [f'color:{g(s, "title_color", "#000")}', "margin:0"]
    return f'<h1 style="{";".join(css)}">{p.get("title", "Post title")}</h1>'


def w_post_excerpt(s):
    p = (_posts_data() or [{}])[0]
    css = typo_css(s) + [f'color:{g(s, "excerpt_color", "#000")}', "margin:0"]
    return f'<p style="{";".join(css)}">{p.get("excerpt", "")}</p>'


def w_post_content(s):
    p = (_posts_data() or [{}])[0]
    css = typo_css(s) + [f'color:{g(s, "text_color", "#000")}']
    return f'<div class="te" style="{";".join(css)}">{p.get("content", "")}</div>'


def w_post_featured(s):
    p = (_posts_data() or [{}])[0]
    r = box(g(s, "image_border_radius")) or "0"
    if not p:
        return ""
    return (f'<img src="{os.path.join(IMG_ROOT, p["image"])}" alt="" '
            f'style="width:100%;height:360px;object-fit:cover;display:block;'
            f'border-radius:{r}">')


def w_post_info(s):
    p = (_posts_data() or [{}])[0]
    css = typo_css(s) + [f'color:{g(s, "text_color", "#A8B6DE")}',
                         "display:flex", "gap:18px", "margin:0"]
    bits = [p.get("date", ""), p.get("category", "")]
    return (f'<div style="{";".join(css)}">'
            + "".join(f"<span>{b}</span>" for b in bits if b) + "</div>")


def w_form(s):
    """Elementor Pro's form widget, rendered statically.

    The real widget builds its fields from `form_fields`; this mirrors the
    markup closely enough to judge the card's height, the two-up row and the
    button, which is all a design preview needs from it.
    """
    lab_css = ";".join(typo_css(s, "label_") +
                       [f"color:{g(s, 'label_color', '#0A1551')}",
                        "display:block", "margin:0 0 6px"])
    fld_css_base = typo_css(s, "field_") + [
        f"color:{g(s, 'field_text_color', '#0A1551')}",
        f"background:{g(s, 'field_background_color', '#fff')}",
        "width:100%", "box-sizing:border-box", "padding:12px 14px",
        "appearance:none",
    ]
    bw = g(s, "field_border_width")
    if isinstance(bw, dict):
        u = bw.get("unit", "px")
        fld_css_base.append(f"border:{bw.get('top', 1)}{u} solid "
                            f"{g(s, 'field_border_color', '#D3D9E8')}")
    r = box(g(s, "field_border_radius"))
    if r:
        fld_css_base.append(f"border-radius:{r}")
    fld_css = ";".join(fld_css_base)

    row_gap = unit(g(s, "row_gap"), "15px")
    col_gap = unit(g(s, "column_gap"), "0px")

    cells = []
    for f in s.get("form_fields", []):
        # the field's own width % at this breakpoint, Elementor's own keys
        wkey = {"desktop": "width", "tablet": "width_tablet",
                "mobile_extra": "width_mobile_extra",
                "mobile": "width_mobile"}[BP]
        order = {"desktop": ["width"],
                 "tablet": ["width_tablet", "width"],
                 "mobile_extra": ["width_mobile_extra", "width_tablet", "width"],
                 "mobile": ["width_mobile", "width_mobile_extra",
                            "width_tablet", "width"]}[BP]
        pct = "100"
        for k in order:
            if f.get(k):
                pct = f[k]
                break
        label = html.escape(f.get("field_label", ""))
        ph = html.escape(f.get("placeholder", ""))
        if f.get("field_type") == "select":
            opts = (f.get("field_options", "") or "").split("\n")
            inner = (f'<div style="{fld_css};color:#8A93B8">'
                     f'{html.escape(opts[0] if opts else "")}'
                     f'<span style="float:right">&#9662;</span></div>')
        elif f.get("field_type") == "textarea":
            inner = f'<div style="{fld_css};min-height:90px;color:#A2AAC4">{ph}</div>'
        else:
            inner = f'<div style="{fld_css};color:#A2AAC4">{ph}</div>'
        cells.append(
            f'<div style="width:calc({pct}% - '
            f'{"0px" if pct == "100" else col_gap}/1);flex:0 0 auto;'
            f'box-sizing:border-box">'
            f'<label style="{lab_css}">{label}</label>{inner}</div>')

    btn_css = typo_css(s, "button_") + [
        f"color:{g(s, 'button_text_color', '#fff')}",
        f"background:{g(s, 'background_color', '#053480')}",
        "display:block", "width:100%", "text-align:center", "border:0",
        "box-sizing:border-box",
    ]
    bp_ = box(g(s, "button_text_padding"))
    if bp_:
        btn_css.append(f"padding:{bp_}")
    br = box(g(s, "button_border_radius"))
    if br:
        btn_css.append(f"border-radius:{br}")
    cells.append(f'<div style="width:100%;flex:0 0 auto">'
                 f'<div style="{";".join(btn_css)}">'
                 f'{html.escape(s.get("button_text", "Submit"))}</div></div>')

    wrap = (f'display:flex;flex-wrap:wrap;gap:{row_gap} {col_gap};'
            f'width:100%;' + ";".join(common(s)))
    return f'<div style="{wrap}">' + "".join(cells) + "</div>"


def w_divider(s):
    w = unit(g(s, "weight"), "1px")
    c = g(s, "color", "#E3E6EF")
    gp = unit(g(s, "gap"), "15px")
    return (f'<div style="padding:{gp} 0;width:100%">'
            f'<div style="border-top:{w} solid {c};width:100%"></div></div>')


def w_accordion(s):
    """Accordion previewed open — a preview exists to show the copy, and a
    stack of collapsed titles shows none of it. Elementor renders the same
    titles and bodies; only the initial state differs."""
    tc = g(s, "title_color", "#0A1551")
    cc = g(s, "content_color", BODY_C)
    bw = unit(g(s, "border_width"), "1px")
    bc = g(s, "border_color", "#E3E6EF")
    tf = unit(g(s, "title_typography_font_size"), "18px")
    cf = unit(g(s, "content_typography_font_size"), "16px")
    ic = g(s, "icon_color", "#053480")
    out = [f'<div style="width:100%;border:{bw} solid {bc};border-radius:6px;'
           f'overflow:hidden">']
    for i, t in enumerate(g(s, "tabs", []) or []):
        top = "" if i == 0 else f"border-top:{bw} solid {bc}"
        out.append(
            f'<div style="{top}">'
            f'<div style="display:flex;justify-content:space-between;gap:16px;'
            f'padding:18px 20px;color:{tc};font-size:{tf};font-weight:600;'
            f'line-height:1.4">'
            f'<span>{t.get("tab_title","")}</span>'
            f'<span style="color:{ic}">&minus;</span></div>'
            f'<div class="te" style="padding:4px 20px 20px;color:{cc};'
            f'font-size:{cf};line-height:1.65">{t.get("tab_content","")}</div>'
            f'</div>')
    out.append("</div>")
    return "".join(out)


def w_map(s):
    """Google Maps widget. The real thing is a third-party iframe; the preview
    draws its footprint so the section's height and layout are honest without
    calling Google from a static file."""
    h = unit(g(s, "height"), "360px")
    return (f'<div style="width:100%;height:{h};border-radius:12px;'
            f'background:#DDE3F0;display:flex;align-items:center;'
            f'justify-content:center;color:#7A83A0;font-size:14px">'
            f'[map: {html.escape(str(g(s, "address", "")))}]</div>')


def w_html(s):
    """Raw HTML widget. JSON-LD and other <script>/<style> payloads are not
    painted, and must not execute inside a preview, so nothing is emitted."""
    return ""


BODY_C = "#4A5378"

WIDGETS = {"heading": w_heading, "text-editor": w_text, "image": w_image,
           "button": w_button, "form": w_form, "star-rating": w_stars, "icon-list": w_icon_list,
           "posts": w_posts, "theme-post-title": w_post_title,
           "theme-post-excerpt": w_post_excerpt,
           "theme-post-content": w_post_content,
           "theme-post-featured-image": w_post_featured,
           "post-info": w_post_info, "divider": w_divider,
           "accordion": w_accordion, "html": w_html,
           "google_maps": w_map}


# ------------------------------------------------------------------ tree
MAXW_FALLBACK = 1240


def render_container(n):
    s = n.get("settings", {})
    kids = "".join(render(c) for c in n.get("elements", []))
    dirn = g(s, "flex_direction", "column")
    css = ["display:flex", f"flex-direction:{dirn}",
           f"align-items:{g(s, 'flex_align_items', 'stretch')}"]
    jc = g(s, "flex_justify_content")
    if jc:
        css.append(f"justify-content:{jc}")
    if g(s, "flex_wrap"):
        css.append(f"flex-wrap:{g(s, 'flex_wrap')}")
    fg = g(s, "flex_gap")
    if isinstance(fg, dict):
        u = fg.get("unit", "px")
        row_g = fg.get("row", fg.get("size", 0))
        col_g = fg.get("column", fg.get("size", 0))
        css.append(f"gap:{row_g}{u} {col_g}{u}")
    p = box(g(s, "padding"))
    if p:
        css.append(f"padding:{p}")
    w = unit(g(s, "width"))
    if w:
        css.append(f"width:{w}")
        css.append("flex:0 0 auto")
    mh = unit(g(s, "min_height"))
    if mh:
        css.append(f"min-height:{mh}")
    css += decor(s) + common(s)

    if n.get("isInner"):
        return f'<div style="{";".join(css)}">{kids}</div>'

    # top-level section: full-bleed background, boxed inner
    outer = ["width:100%"] + decor(s)
    boxed = unit(g(s, "boxed_width"), f"{MAXW_FALLBACK}px") \
        if g(s, "content_width", "boxed") == "boxed" else "100%"
    inner_css = [c for c in css if not c.startswith("background")
                 and not c.startswith("border-radius")]
    inner_css += [f"max-width:{boxed}", "margin:0 auto", "width:100%",
                  "box-sizing:border-box"]
    return (f'<section style="{";".join(outer)}">'
            f'<div style="{";".join(inner_css)}">{kids}</div></section>')


def render(n):
    if hidden(n.get("settings", {})):
        return ""
    if n.get("elType") == "widget":
        fn = WIDGETS.get(n.get("widgetType"))
        return fn(n.get("settings", {})) if fn else ""
    return render_container(n)


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:'Montserrat',system-ui,sans-serif;background:{bg}}}
.te p{{margin:0 0 0.8em}} .te p:last-child{{margin-bottom:0}}
.te a{{color:inherit}}
h1,h2,h3,h4{{margin:0}}
</style></head><body>{body}</body></html>"""


def main():
    path = sys.argv[1]
    global BP
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
    BP = ("mobile" if width <= 767 else
          "mobile_extra" if width <= 880 else
          "tablet" if width <= 1024 else "desktop")
    doc = json.load(open(os.path.join(ROOT, path)))
    body = "".join(render(s) for s in doc["content"])
    bg = doc.get("page_settings", {}).get("background_color", "#FFFFFF")
    sys.stdout.write(PAGE.format(bg=bg, body=body))


if __name__ == "__main__":
    main()
