---
name: elementor-clone-build
description: "Rebuild a website page or site from a reference URL or PDF as native Elementor / Elementor Pro (Flexbox Container) JSON templates that hit 100 PageSpeed and are fully SEO-optimised. Use whenever Adam asks to clone, replicate, rebuild, recreate or convert a site/page/PDF design into Elementor, WordPress or a template JSON, even if he doesn't say 'Elementor'."
---

# Elementor Clone Build

Turn a reference (live URL or PDF) into a pixel-faithful Elementor site that is built entirely from native Elementor widgets and Style-tab settings, scores 100 on PageSpeed Insights, and is properly SEO'd even when the reference isn't. Work is done as **generated JSON** pushed to the site with WP-CLI, not by dragging widgets in a browser. Keep it cheap on credits: text specs over screenshots, one generator script reused for every page, decisions made once in a spec and never re-litigated.

Target stack: WordPress + Elementor core + Elementor Pro 4.2.0, **Flexbox Container** editor (not V4 Atomic), 20i hosting with 20i's StackCache plugin and SSH/WP-CLI access. The project folder lives on Adam's Mac (connect it to the session); GitHub is optional. Adam checks PageSpeed Insights manually and pastes scores back.

## The seven rules (never break these without Adam's written OK)

1. **Native widgets only.** Heading, Text Editor, Image, Button, Icon, Icon Box, Icon List, Image Box, Container, Nested Tabs/Accordion, Pro Form, Posts/Loop Grid, Testimonial Carousel, Call to Action, etc. No HTML widget, no code block, no shortcode wrappers, no inline `style=` in Text Editor content. The site must stay editable by Adam and his clients in the normal Elementor UI.
2. **Style-tab styling only.** Every colour, font, size, spacing, border, shadow, hover state and breakpoint value lives in the widget/container settings (and Site Settings globals). Custom CSS (Advanced > Custom CSS, Site Settings > Custom CSS, theme CSS) is a last resort: stop, explain exactly what can't be done natively and why, and wait for approval before adding a single line.
3. **Pixel fidelity to the reference** at desktop (1440), tablet (1024/768) and mobile (390). Match layout, spacing rhythm, type scale, colours and imagery. Copy and structure are reproduced faithfully unless Adam asks for changes.
4. **Responsive styles are always delivered, never assumed.** If the reference is a live site, capture and preserve its real tablet and mobile behaviour. If the reference has no responsive version (a PDF, a desktop-only mockup, a broken mobile layout), design the tablet and mobile breakpoints from scratch following the Responsive Rules below, and say in the spec which sections were designed rather than copied. A page with only desktop values set is not finished.
5. **Spacing uses the scale, not one-off numbers.** Every padding, margin and gap value is a token from the Spacing Scale below (Atlassian's 8 px system). Reference values are snapped to the nearest token; anything that would move more than 4 px is listed at Gate A so Adam decides fidelity vs. rhythm.
6. **100 PageSpeed and full SEO are part of "done"**, not a later phase. Decisions that hurt performance (sliders, video backgrounds, motion effects, third-party embeds above the fold, unoptimised images, extra font weights) are avoided in the spec, not fixed afterwards.
7. **Approve once, run to completion.** Get sign-off at the two gates below, then finish the whole page/site without asking for click-by-click permission. Amendments come during or after.

**Approval gates:** (A) after the Section Spec is written, before any JSON is generated; (B) any time custom CSS/HTML, site-side PHP, or a deviation from the reference is proposed. Everything else runs unattended.

## Inputs to collect first (one message, all at once)

Ask only for what's missing; don't re-ask things already in the conversation.

- Reference: URL(s) or PDF path. Which pages are in scope. Header/footer in scope or not (default: out of scope, they are Theme Builder templates handled separately).
- Target site: staging URL (a 20i staging package or subdomain, kept on `noindex` until go-live), and how it is reached: SSH host/user for WP-CLI (preferred), or a WordPress Application Password for the REST route. Both run from Adam's Mac via the local shell, or Adam runs the pasted script himself; the cloud sandbox cannot SSH out.
- Confirm Elementor core version and that Flexbox Containers is the active editor. Ask for **one exported template JSON from that site** (Templates > Saved Templates > Export). This is the schema ground truth: match its `version` field, id format and settings keys rather than trusting documentation.
- SEO plugin in use (Rank Math / Yoast / SEOPress) and the client's target keywords, location and business type, if known.
- Brand tokens if they exist already (colour hexes, font families). Otherwise they get extracted in Phase 1.
- Project folder on Adam's Mac (connect it to the session). Start every new client from the kit repo `ignitecreativenw-sketch/Elementor-Claude-builder` (clone or copy it to `~/Desktop/<Client>`); it already contains the generator, capture, QA and push scripts. A git repo inside the client folder is optional.

```
<project>/
  reference/        screenshots (3 widths), combined.css, design-tokens.json, content.json, pdf pages
  spec/             one <page>.md Section Spec per page (the contract); spec/forms/<name>.json for FormCraft forms
  build/            build_template.py, build_form.py (FormCraft), capture_reference.py, capture_shots.py, qa_diff.py, responsive_audit.py, render_preview.py, download_assets.py
  templates/        <page>.json outputs (what gets pushed to the site); templates/forms/<name>.txt FormCraft imports
  assets/           optimised images (webp/svg) + manifest.json (file, alt)
  deploy/           push_page.sh (SSH), push_rest.py (REST), push_seo.py, sync_media.py, verify_live.py, set_breakpoints.py, .env (gitignored), media-map.json, pages.json
  qa/               screenshot diffs, psi.md, seo-checklist.md, perf-checklist.md, design-checklist.md
  tools/            shallow clones of ui-ux-pro-max-skill and impeccable (see Design Standards), gitignored
```

## Design Standards (spacing, craft floor, design intelligence)

These standards come from three sources and apply to every build: Atlassian's spacing foundation, Impeccable's craft floor, and UI UX Pro Max's design-system generator. The reference still wins on what the page looks like; the standards decide the values used to build it and fill every gap the reference leaves.

### Spacing Scale (Atlassian, 8 px base)

| Token | px | Use for |
|---|---|---|
| space.0 | 0 | flush |
| space.025 | 2 | icon/text hairline gaps |
| space.050 | 4 | small compact UI: icon-to-label, inside badges |
| space.075 | 6 | compact component padding |
| space.100 | 8 | component padding, tight sibling gaps, inside cards |
| space.150 | 12 | button vertical padding, list item gaps |
| space.200 | 16 | button horizontal padding, card padding, paragraph gaps |
| space.250 | 20 | mobile side gutters, form field gaps |
| space.300 | 24 | card padding (roomy), gaps between related blocks |
| space.400 | 32 | gaps between distinct groups, column gaps on tablet |
| space.500 | 40 | column gaps on desktop, heading-to-block separation |
| space.600 | 48 | section padding on mobile |
| space.800 | 64 | section padding on tablet, gaps between major blocks |
| space.1000 | 80 | section padding on desktop (use 2 × space.600 = 96 or space.1000 + space.500 = 120 for hero-scale sections) |

Rules: small range (0–8) inside components; medium range (12–24) for component padding and sibling spacing; large range (32–80) for layout and sections. Group by proximity (related things close, unrelated things far), keep a deliberate contrast between tight and generous intervals rather than one value repeated everywhere, and put more space above a heading than below it. Negative margins are allowed only to overlap deliberately (a card breaking out of a band) and must be a scale value. Optical adjustments off-scale are permitted only after a screenshot shows the need, and get noted in the spec.

Snapping a reference: measure the computed value, choose the nearest token; ties round toward the larger token for section padding and the smaller for component padding. Record `measured → token` in the spec so Adam can see every move. In the generator, expose the scale as constants (`SP = {0:0, 25:2, 50:4, 75:6, 100:8, 150:12, 200:16, 250:20, 300:24, 400:32, 500:40, 600:48, 800:64, 1000:80}`) and never write a literal px value for padding/margin/gap.

### Craft floor (from Impeccable, adapted for Elementor)

Verify on the built page, in the same screenshot round as the diff check, not as separate trips:

- Contrast: body and placeholder text ≥ 4.5:1, large text ≥ 3:1. Secondary text on a coloured surface is tinted from that surface's hue, never plain grey.
- Depth: shadows carry an offset and a soft blur (Style > Box Shadow with y-offset and blur, not a flat halo).
- Type: body measure 65–75 characters (set max-width on Text Editor widgets), obvious scale and weight steps, headings balanced (no single-word orphan line at any breakpoint), nothing under 14 px on mobile.
- Motion: none by default (performance rule). If the brief earns one authored moment, it is a single hover transition on Style controls, not entrance animations on every section.
- States: button hover, form focus/error states, empty states for dynamic widgets, all styled from Style tab controls.
- Browser surfaces: text-selection colour, link underline offset and focus ring are set in Site Settings so the page reads as designed rather than assembled.

Refuse by default (the reference or Adam's brief can earn any of them back, except the first): a kicker/eyebrow label above a heading; nested cards or same-size icon-heading-text cards as the page skeleton when the reference didn't have them; gradient text; glass/blur as decoration; coloured left/right borders thicker than 1 px on cards; hard zero-blur offset shadows; monospace as a "technical" costume; emoji or unicode glyphs as icons (use Elementor's icon library or SVG); system display fonts as the headline voice.

### Design intelligence (UI UX Pro Max)

Use it when the reference does not decide something: a PDF with no responsive version, a missing section, a weak or absent brand system, or when Adam asks for a new page with no reference. Clone once per project into `tools/` and query it; it runs on Python 3 with no dependencies:

```bash
git clone -q --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill tools/ui-ux-pro-max-skill
python3 tools/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "<industry> <product type> <keywords>" --design-system -p "<Client>" --density 3
python3 tools/ui-ux-pro-max-skill/src/ui-ux-pro-max/scripts/search.py "<one concern>" --domain ux     # e.g. "badge chip label wraps", "error summary validation"
```

`--design-system` returns a pattern, style, palette, font pairing, effects, anti-patterns and a pre-delivery checklist; `--density 3` keeps the spacious marketing-page spacing that matches the Spacing Scale. Treat its output as a proposal: put the parts you adopt into the spec header (Globals/Fonts) and `qa/design-checklist.md`, never paste the whole report. If the reference already has a brand system, skip it; if the reference's fonts are a performance problem (5+ weights, a non-web-safe display face), use its font-pairing search to propose a metric-compatible replacement at Gate B. Its stack guidance (React, Tailwind…) does not apply here; only style, colour, typography, UX and landing-page pattern domains do.

Impeccable's deterministic detector can run against the built staging page as an extra QA pass when the launcher is available (`tools/impeccable/.claude/skills/impeccable/scripts/impeccable detect --json --scope layout <saved-html-dir>` on a saved copy of the staging page). It reports mechanical tells (arbitrary spacing, grey-on-colour text, nested cards); act on its findings, don't re-audit by hand. Skip it silently if the binary can't download in the sandbox.

## Phase 1 — Capture the reference (cheap, text-first)

Goal: a compact, text-based description of the reference so later phases (and smaller models) never need the raw page in context.

**URL reference** — run `build/capture_reference.py <url>` (Playwright; reuse and extend, don't rewrite) so that it:

- Loads with `wait_until="load"` and a 30 s timeout, not `networkidle` (sites with persistent connections hang forever). If the site crashes (some run stale Slider Revolution), simply re-run.
- Takes full-page screenshots at 1440, 1024 and 390 wide. Save to `reference/`. Only open a screenshot with Read when a visual decision genuinely needs it; prefer the text outputs.
- Dumps `design-tokens.json` **per breakpoint**: at each of the three widths, every distinct colour, font-family, font-size/weight/line-height per heading level and body, container max-width, section paddings, gaps, button styles, border radii, shadows, and per section whether it stacks, reorders, hides, or changes alignment. Read computed styles from real elements at that viewport, not stylesheets. Include a `spacing_snap` table: each measured padding/gap with its nearest Spacing Scale token and the delta.
- Dumps `content.json`: sections in DOM order, each with heading text, paragraphs, buttons (label + href), images (src, alt, rendered width×height at each breakpoint), lists, and any form fields.
- Saves `combined.css` for reference only.
- Uses paths relative to the script file, not the terminal cwd.

**PDF reference** — `pdftoppm -r 150 -png` for page images, `pdftotext -layout` for copy, `pdffonts` for font families, and sample colours from the page images with Python/PIL. Rendered size for a print PDF: treat the page width as the 1440 desktop canvas and scale proportionally; state that scale factor in the spec. A PDF has no tablet/mobile version: mark every section `responsive: designed` and apply the Responsive Rules; run the UI UX Pro Max design-system search for the client's industry to fill gaps the PDF leaves (hover states, form styling, missing sections).

Do not paste `combined.css` or full screenshots into the conversation. The deliverable of this phase is the tokens file and the content file.

## Responsive Rules (used when the reference gives nothing to copy)

Apply these when the reference is a PDF, is desktop-only, or its mobile layout is broken. Write the resulting values into the spec so they are explicit, not implied. All spacing values are Spacing Scale tokens.

- Breakpoints: Elementor defaults — tablet ≤ 1024, mobile ≤ 767. Set values for desktop, tablet and mobile on every container and on any widget whose desktop size wouldn't survive at 390 px.
- Type scale: H1 desktop × 0.72 on tablet, × 0.57 on mobile (56 → 40 → 32); H2 × 0.8 / 0.65; H3 and below × 0.9 / 0.85; body stays 16–18 px everywhere; line-height 1.1–1.2 for display headings, 1.5–1.65 for body. Never below 14 px on mobile.
- Section padding: desktop space.1000 or 96/120 for hero-scale → tablet space.800 → mobile space.600; horizontal padding space.250 (20) on mobile so content never touches the edge.
- Gaps: column gap desktop space.500 → tablet space.400 → mobile space.300; inside cards space.200/space.300.
- Rows: 3+ columns → 2 on tablet → 1 on mobile; 2 columns → 1 on mobile (keep 2 on tablet only if each column stays ≥ 320 px). Use `flex_direction_mobile: column` and full-width children; don't rely on wrap for two-item rows.
- Order: text before image on mobile for hero and feature sections unless the image carries the message; use Flex order per breakpoint, not duplicated widgets.
- Alignment: centre-align hero and CTA text on mobile; keep body content left-aligned.
- Images: hero max height 60 vh on mobile with `object-fit: cover` via the Image widget's height control; card images keep their desktop ratio.
- Buttons: full-width or stacked with space.150 (12) gap on mobile when two sit side by side; tap targets ≥ 44 px tall.
- Hide nothing on mobile that carries content; decorative elements (large background shapes, side images) may be hidden per breakpoint with Responsive > Hide On Mobile.

## Phase 2 — Section Spec (Gate A)

Write `spec/<page>.md`. This is the single contract every later step follows; a lower model should be able to generate the JSON from it without looking at the reference again. Keep it terse. Format:

```
# <Page> — Section Spec
Canvas: 1440 desktop / 1024 tablet / 390 mobile. Container max-width: 1200px.
Globals: primary #8F0000, accent #FDB415, text #222222, surface #F7F7F7
Fonts: Headings Poppins 600 | Body Inter 400 (weights used: 400, 600 only)
Responsive source: captured (URL) | designed (PDF/desktop-only) — per section below
Spacing snaps > 4px: S1 padding 116 → 120 (space.1000+500); S3 gap 28 → 32 (space.400)

## S1 Hero  [responsive: captured]
Layout: container, full-width bg, boxed content, row → column on mobile, gap 500/400/300
Bg: image hero.webp (1920×900, LCP image — use Image widget not bg where possible)
Padding: 120/0/120/0 desktop, 800/0/800/0 tablet, 600/250/600/250 mobile   (tokens)
Widgets:
  H1 "Year-end accounts made simple" — 56/1.1 desktop, 40 tablet, 32 mobile, #fff, center
  Text "..." — 18/1.6, #fff, max-width 640; 16 mobile
  Button "Get a quote" → /contact — primary, radius 6, padding 150/300, hover accent; full-width mobile
SEO: H1 (only one on page). Image alt: "..."
Perf: no animation, fetchpriority high on hero image

## S2 Services grid  [responsive: designed]
...
```

For each section record: container layout (direction, wrap, justify/align, gap, widths) at all three breakpoints, background, padding per breakpoint as tokens, the widget list with content and the specific Style-tab values per breakpoint where they differ, and the SEO/perf notes. Map every reference pattern to a native widget using this table; if something has no row, flag it as a Gate B item in a "Needs approval" list at the bottom of the spec.

| Reference pattern | Elementor widget / approach |
|---|---|
| Heading / paragraph | Heading / Text Editor (use Text Editor for rich paragraphs, Heading for anything that is a heading semantically) |
| Icon + title + text cards | Icon Box (or Image Box for image cards) inside a wrapping row container |
| Bulleted feature lists with ticks | Icon List |
| CTA banner | Container with bg + Heading + Button (Call to Action widget only if it matches better) |
| Stats / counters | Counter widget, animation off |
| Tabs / accordion / FAQ | Nested Tabs / Nested Accordion (FAQ schema via SEO plugin) |
| Testimonials | Testimonial Carousel (autoplay off, lazy) or static Testimonial widgets in a grid |
| Logo strips | Image widgets in a wrapping row (not a carousel) |
| Forms | Elementor Pro Form by default; FormCraft (via Shortcode widget) when the brief needs conditional logic, calculations, multi-step or popup forms — see Forms |
| Blog/post grids | Loop Grid with a Loop Item template |
| Sliders / hero carousels | Replace with a static hero; propose this deviation at Gate B |
| Video backgrounds, parallax, Lottie, entrance animations | Omit; propose a static equivalent at Gate B |
| Google Maps embed | Static map image linking to Google Maps; propose at Gate B |
| Decorative dividers, spacing hacks | Container padding/margin and gap, never Spacer widgets or empty containers |
| Overlapping/absolute elements | Container with Advanced > Position: absolute/custom, still native; note it explicitly and give it a mobile fallback (usually static) |

Present the spec, the deviations list, the spacing snaps over 4 px, the designed-responsive sections and the Gate B items to Adam in one message and stop until approved.

## Phase 3 — Site Settings first, then generate JSON

**Site Settings (do once per site):** global colours and global fonts named from the tokens (Primary, Secondary, Text, Accent, Surface…), default typography per heading level, default button style, container width and default gap (space.500), default padding, link/selection/focus colours. Push them with `wp elementor kit import <kit.zip>` if a kit exists, otherwise set them in the editor once; `deploy/set_breakpoints.py` sets the breakpoints over REST. Every widget then references globals so JSON stays tiny, consistent, and a client colour change is one edit. Also Site Settings > Performance: load Google Fonts locally; Elementor > Settings > Features: Optimized Markup, Improved CSS/Asset loading, Element caching, Inline font icons, Lazy load background images.

**Generator:** extend `build/build_template.py` (helpers `container(...)`, `heading(...)`, `text(...)`, `image(...)`, `button(...)`, `icon_box(...)`, `responsive(key, desktop, tablet, mobile)`, and the `SP` spacing constants) with one `build_<page>()` per page that transcribes the Section Spec into a call tree. `responsive()` must always write all three keys when tablet/mobile values are given; a missing `_mobile` value in the output is a bug. Padding/margin/gap helpers accept token keys only (`pad(SP[1000], 0, SP[1000], 0)`), so an off-scale value is a type error, not a silent drift. `image()` looks up `deploy/media-map.json` and writes `{"url": ..., "id": <attachment id>}` so Elementor outputs srcset and width/height. Emit `templates/<page>.json`. Generating from code rather than hand-writing JSON keeps ids unique, keys correct and iterations cheap (change one helper, regenerate every page).

Schema skeleton (verify keys against Adam's sample export before relying on it):

```json
{
  "version": "0.4",
  "title": "Home",
  "type": "page",
  "page_settings": [],
  "content": [
    {
      "id": "a1b2c3d", "elType": "container", "isInner": false,
      "settings": {
        "content_width": "boxed",
        "flex_direction": "row", "flex_direction_mobile": "column",
        "flex_gap": {"unit": "px", "size": 40, "column": "40", "row": "40", "isLinked": true},
        "flex_gap_mobile": {"unit": "px", "size": 24, "column": "24", "row": "24", "isLinked": true},
        "padding": {"unit": "px", "top": "120", "right": "0", "bottom": "120", "left": "0", "isLinked": false},
        "padding_tablet": {"unit": "px", "top": "64", "right": "0", "bottom": "64", "left": "0", "isLinked": false},
        "padding_mobile": {"unit": "px", "top": "48", "right": "20", "bottom": "48", "left": "20", "isLinked": false},
        "background_background": "classic",
        "__globals__": {"background_color": "globals/colors?id=primary"}
      },
      "elements": [
        {
          "id": "b2c3d4e", "elType": "widget", "widgetType": "heading",
          "settings": {
            "title": "Year-end accounts made simple", "header_size": "h1", "align": "center",
            "typography_typography": "custom",
            "typography_font_size": {"unit": "px", "size": 56},
            "typography_font_size_tablet": {"unit": "px", "size": 40},
            "typography_font_size_mobile": {"unit": "px", "size": 32},
            "typography_line_height": {"unit": "em", "size": 1.1},
            "__globals__": {"title_color": "globals/colors?id=white", "typography_typography": "globals/typography?id=primary"}
          },
          "elements": []
        }
      ]
    }
  ]
}
```

Conventions: ids are 7-char lowercase hex, unique across the file; responsive values use `_tablet` / `_mobile` suffixes; `isInner: true` for nested containers; two-item rows use exactly two direct children with `justify-content: space-between` rather than flex-shrink/wrap tweaks.

Also generate `qa/seo-checklist.md`, `qa/perf-checklist.md` and `qa/design-checklist.md` (craft floor items plus any UI UX Pro Max pre-delivery items adopted) for the page so QA is a tick-list, not a judgement call.

## Phase 4 — Push to the site (SSH + WP-CLI first, REST second, browser last)

No import dialog. Credentials live in `deploy/.env` (gitignored, never pasted into chat). Run the push from Adam's Mac shell or hand Adam the one-line command; wait for confirmation before QA.

**Route A — `deploy/push_page.sh <template> "<Title>" <slug>` (SSH + WP-CLI, preferred on 20i).** It scp's `assets/*.webp` and `templates/<page>.json` to the server, runs `wp media import` for anything not already in the library (alt text from `assets/manifest.json`), rewrites `deploy/media-map.json`, regenerates the template with real attachment IDs, then creates or updates the page by writing `_elementor_edit_mode`, `_elementor_template_type`, `_elementor_version` and `_elementor_data` (the JSON `content` array) with `wp post meta update`, and flushes Elementor CSS. Page IDs are stored in `deploy/pages.json` so re-pushes update in place.

**Route B — `python3 deploy/push_rest.py <template> "<Title>" <slug>` (REST API with an Application Password) when the host has no SSH.** Same steps over HTTPS: `POST /wp/v2/media` for assets, `POST /wp/v2/pages` with the Elementor meta (Elementor 4.x exposes `_elementor_data` to REST, no mu-plugin needed), `DELETE /elementor/v1/cache`. It backs off and retries through the host's bot-protection interstitial. `deploy/push_seo.py` sets titles/descriptions the same way; `deploy/verify_live.py` confirms the page rendered.

**Route C — browser fallback** only when neither works: Media > Add New in bulk, then Templates > Saved Templates > Import Templates and insert into the page, driven through Claude in Chrome (Adam's browser).

After any push: purge StackCache (`wp cache flush` plus the plugin's purge, or the My20i button) before any screenshot or PSI run. `wp elementor library import` is optional for a reusable library copy.

**Visual QA loop** (after each push, one batched round, at most two):
- `build/capture_shots.py` screenshots the staging page at 1440, 1024 and 390; `build/qa_diff.py` compares with the reference shots and reports a diff percentage per section per breakpoint. For `responsive: designed` sections there is no mobile reference to diff against, so `build/responsive_audit.py` checks them against the Responsive Rules instead: no horizontal overflow, nothing clipped, no text under 14 px, tap targets ≥ 44 px, stacking order as specified.
- In the same round, run the craft-floor checks and tick `qa/design-checklist.md`; optionally run the Impeccable detector on the saved staging HTML.
- Fix structural or repeated problems in the generator and re-push. Fix one-off nudges directly in the editor only if Adam prefers; otherwise everything goes through JSON so the project folder stays the truth.
- Stop iterating when each captured section is under the agreed diff threshold (default 2 % RMSE per section, all three widths), every designed section passes the rules check, and the design checklist is ticked, or when the remaining difference is an approved deviation. Do not keep polishing past the second round.

## Forms (Elementor Pro Form by default, FormCraft when it earns it)

**Default:** Elementor Pro Form widget for contact, quote-request, callback and newsletter forms. It is native, styled in the Style tab, adds no plugin assets, and the honeypot option avoids reCAPTCHA. Recipients, subject and the success message go in the widget settings in the generated JSON.

**FormCraft** (nCrafts, premium) is used only when the brief needs conditional show/hide logic, live maths/quote calculators, multi-step forms, popup or slide-in forms with triggers, or per-form analytics. It is a separate front end (own CSS/JS, AJAX submit), so each FormCraft form is one extra script/style pair to account for in the PageSpeed loop, and its look is set in its own colour scheme (from the Site Settings globals), not the Style tab.

How FormCraft forms are built and placed:

1. Write a form spec at `spec/forms/<name>.json` (copy `spec/forms/contact.example.json`): name, recipients, sender, success message, colours from the globals, fields (`text`, `email`, `textarea`, `dropdown`, `date`, `submit`, `captcha`). Other field types are added in the FormCraft UI after import, or exported from a sample form so their markup can be added to the generator.
2. `python3 build/build_form.py spec/forms/<name>.json` writes `templates/forms/<name>.txt`, a FormCraft 3 import file (JSON with raw-deflate + base64 `html`/`builder` blobs, plus `meta_builder` and `addons`). The generator never writes SMTP credentials; mail goes through the site's PHP mail / SMTP plugin. The reCAPTCHA secret is entered in FormCraft > Add-ons by Adam, never in a spec or the repo.
3. Import: FormCraft > Add New > Import > choose the `.txt` > name it > Create Form (Adam or Claude in Chrome; ~20 seconds). Open the form once in the FormCraft editor and press Save so the stored HTML is recompiled against the real form id. Note the id.
4. Embed with the native Elementor Shortcode widget in the page JSON: `{"widgetType": "shortcode", "settings": {"shortcode": "[fc id='<id>'][/fc]"}}`. Popup trigger: `[fc id='<id>' type='popup' placement='inline']Get a quote[/fc]`. Record the id in `deploy/pages.json` under `forms`.
5. QA: submit a test entry on staging; check the notification arrives, the success message shows, no console errors, and PSI after the form is on the page.

Secrets rule: FormCraft exports contain the SMTP username/password and reCAPTCHA secret if they were set in the UI. Never commit a raw export; strip `smtp_*` and `secret_key` first (`build_form.py --scrub <export.txt>` does this) and treat any pasted export as a credential leak to rotate.

## Phase 5 — SEO (done even if the reference has none)

Per page, fill and tick `qa/seo-checklist.md`:

- Title tag ≤ 60 chars, primary keyword first, brand last. Meta description 120–155 chars with a call to action. Set via `deploy/push_seo.py` or `wp post meta update $ID rank_math_title ...` / `_yoast_wpseo_title ...` in the push script.
- Exactly one H1; H2/H3 hierarchy follows content, no heading levels skipped, no headings used just for size (set `header_size` to `div`/`p` on decorative text).
- Slug short and keyworded; canonical set; indexable; OG title/description/image set.
- Every image: descriptive filename, alt text (from `assets/manifest.json`), explicit width/height (pick a registered image size in the widget, not "full", unless it is the hero).
- Internal links in body copy to relevant pages; one clear primary CTA.
- Schema via the SEO plugin: Organization/LocalBusiness site-wide; Service, FAQPage, Article/BreadcrumbList per page as relevant. No JSON-LD pasted into HTML widgets.
- XML sitemap includes the page, robots.txt sane, staging `noindex` removed at go-live and not before.
- Copy: keep reference copy, but if a section has no heading or the H1 is weak, propose SEO'd copy at Gate B rather than silently rewriting.

## Phase 6 — Performance to 100 (Adam runs PSI and pastes the numbers)

**Images:** resize to the largest rendered width × 2 (cap 1920 for hero, 1200 for content, 800 for cards), export WebP quality 75–82 (AVIF if the host serves it), strip metadata. Hero/LCP image: Image widget above the fold, not a container background, so Elementor's Optimized Image Loading can add `fetchpriority="high"` and skip lazy-load. Everything below the fold lazy-loads (default). Logos and icons as SVG (inline font icons enabled).

**Fonts:** at most two families and four weights total. Google Fonts loaded locally or uploaded as custom fonts (WOFF2 only), `font-display: swap`. Don't use a font weight the spec doesn't list.

**Elementor:** disable unused widgets in Elementor > Element Manager (each enabled widget can add CSS/JS). No Motion Effects, entrance animations, parallax, sticky effects, video backgrounds, Lottie, or carousel autoplay unless approved at Gate B. Nested Tabs/Accordion over legacy ones.

**Layout stability (CLS):** all images have dimensions; containers that hold async content get a min-height; pick a metrically similar fallback font.

**Third-party:** nothing third-party above the fold. Maps as static image + link; social feeds (Behold.so / Smash Balloon) loaded on their own section below the fold; analytics/tag managers only via a deferred loader. Contact forms: Elementor Pro Form, honeypot over reCAPTCHA where possible (reCAPTCHA alone can cost 5–10 points).

**20i StackCache:** enable page caching and browser caching, CSS/JS minify; test combine on staging before trusting it (Elementor's optimised loading plus StackCache combine can double-process — if PSI shows render-blocking CSS, switch one of them off). Purge after every push before Adam runs PSI.

**Loop:** after each push, ask Adam for the PSI mobile + desktop scores and the top three "Opportunities"/"Diagnostics" lines. Log them in `qa/psi.md` with the date and what changed. Address the top item, re-push, repeat. Don't guess at scores; don't run Lighthouse yourself unless asked.

## Phase 7 — Done checklist and handover

- All captured sections under diff threshold at three widths; all designed-responsive sections pass the rules check; design checklist ticked; deviations and spacing snaps listed and approved.
- SEO checklist fully ticked; perf checklist fully ticked; PSI 100/100 recorded in `qa/psi.md` (or the exact blocker explained, e.g. a client-mandated chat widget).
- Zero custom CSS/HTML/PHP, or each instance listed with Adam's approval quoted.
- `spec/`, `build/`, `templates/`, `assets/`, `deploy/`, `qa/` saved in the project folder (committed if it is a git repo) with a short note per page.
- One closing message: what was built, page IDs, scores, deviations, anything the client needs to supply (real copy, photos, form recipients).

## Working cheaply on credits (read this if you are a smaller/faster model)

- The Section Spec is the source of truth. Generate JSON from it; don't re-open the reference site or screenshots unless a section fails QA.
- Batch independent tool calls in one turn (all three screenshots, all image conversions, all checklist writes, all media imports in one script run).
- Never paste large files (CSS dumps, full JSON, base64 images, UI UX Pro Max reports) into chat. Write them to disk and mention the path.
- Reuse the kit's scripts; extend them rather than writing raw JSON or ad-hoc shell by hand.
- One QA loop per page at a time, two rounds maximum. Fix the biggest diff first; stop when the threshold is met, not when it "looks perfect".
- Spacing decisions are already made: pick the token, don't deliberate. Off-scale means a Gate A note, not a judgement call.
- If unsure whether something is possible natively, check Elementor's Style/Advanced tab controls for that widget before proposing custom CSS. Most "impossible" things are: Advanced > Position, Advanced > Transform, container Advanced > Custom width, Flex order per breakpoint, Responsive > Hide On, and the Heading widget's HTML tag.
- Escalate (don't decide alone): any custom CSS/HTML/PHP, dropping or changing a reference section, changing copy, adding a plugin, anything that costs PageSpeed points on purpose.
