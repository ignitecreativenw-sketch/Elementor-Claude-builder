# Emil Kowalski's rules, translated for Elementor builds

Source: github.com/emilkowalski/skills @ 2d22863 (Oct 2026), MIT. Fetched at Stage 1 into `tools/emil-skills/`. This file is the subset that applies to a native-Elementor marketing site, each rule mapped to the Elementor control (or the kit component) that implements it. Rules that need React, JS libraries or hand-rolled gestures are left out on purpose.

The three skills we take from: `emil-design-eng` + `review-animations/STANDARDS.md` (motion and polish), `mobile-native` (the platform layer on a phone), `break-ui` (worst-case content). `apple-design` adds the one principle under "feel".

---

## A. Motion floor (emil-design-eng / review-animations)

> Ruling (CONFLICTS #1): these values govern everything interactive when a brief allows motion; the one exception is a single focal hero entrance per page, allowed at 500–800 ms (Impeccable's band), native Fade only.

Our default is no motion (performance rule 6). When motion is allowed — a hover, a button, an accordion opening, a mobile menu, a popup — these values are the only ones used.

| Rule | Why | Elementor implementation |
|---|---|---|
| **Should it animate at all?** Things used tens of times a visit (nav hovers, list hovers) get little or nothing; occasional things (menus, accordions, popups) get standard motion; first-time moments can carry a flourish. | Frequency sets tolerance. Animation on a frequent action reads as lag. | Nav items: colour change only, 150 ms. Mobile menu / popup: one enter transition. No entrance animations on sections (Advanced > Motion Effects off). |
| **Easing: ease-out for anything entering or exiting; ease-in-out for things moving on screen; ease for hover colour; linear only for constant motion. Never ease-in on UI.** | ease-in delays the first frame, which is the frame the user is watching. | Elementor's Style tab exposes duration, not curves, and uses `ease` by default — acceptable for hover colour, which is exactly where `ease` is right. Popups/menus: Elementor's entrance effects use ease-out curves; pick Fade or Slide, never Bounce/Zoom-from-nothing. |
| **Duration: button press 100–160 ms; tooltips/small popovers 125–200; dropdowns/selects 150–250; modals/drawers 200–500. UI stays under 300 ms.** | 180 ms feels more responsive than 400 ms; speed is perceived performance. | Set **Transition Duration** on every Button, Icon Box, Image, Nav Menu hover to **0.15–0.2 s** (Elementor's default 0.3 s is the top of the range, not the middle). Popup / off-canvas menu: 0.25–0.3 s. |
| **Never animate from scale(0). Start ≥ 0.95 with opacity.** | Nothing in the world appears from nothing. | Elementor "Zoom In" entrance starts from 0 — don't use it. Prefer Fade In; if scale is wanted, Pro's custom entrance isn't available natively → stay with Fade. |
| **Hover scale subtle: 1.02–1.05, press 0.95–0.98.** | Feedback, not a performance. | Image / Icon Box hover: Elementor's "Grow" hover animation is ~1.1 — too much; use no hover animation and change colour/shadow instead, or set a Transform > Scale 1.02 on Hover (Advanced > Transform, native). |
| **Only transform and opacity animate.** | Layout/paint properties drop frames. | Hover changes to colour, opacity, shadow and transform are fine; never animate padding, width, height, border width. Elementor hover effects "Shrink/Grow/Float" are transforms — ok at small values. |
| **Stagger 30–80 ms when a group enters; never block interaction while it plays.** | A cascade reads as natural; long delays read as slow. | We don't use entrance animations by default. If a `new` page earns one (Gate B), Elementor's per-widget Animation Delay: 0 / 50 / 100 ms, not 200+. |
| **Reduced motion: keep opacity/colour, drop movement.** | Motion sickness is real. | Elementor honours `prefers-reduced-motion` for its own entrance animations; with none used, we are compliant by construction. Note it in `qa/design-checklist.md`. |
| **Match the motion to the mood.** A professional site is crisp and fast; playful can be bouncier. | Cohesion is what makes it feel finished. | One duration (0.15 s) and one hover language site-wide; set it in Site Settings > Buttons/Links so every widget inherits. |

Elementor-specific **never**: Motion Effects (scroll/mouse), Sticky with transition, entrance animation on more than the hero, "Bounce"/"Rubber band"/"Zoom" effects, hover animations "Bob/Wobble/Buzz/Pulse", background slideshow transitions, Lottie. These are the Elementor equivalents of `transition: all 300ms` + `scale(0)` + bounce easing in one.

## B. Polish floor (emil-design-eng component principles)

| Rule | Elementor implementation |
|---|---|
| Buttons must feel responsive: a visible pressed/hover state with a short transition. | Button > Style > Hover: background + text colour change, Transition Duration 0.15 s. Hover Animation: none. |
| Popovers scale from their trigger; modals from centre. | Elementor Popups (Pro): position centre, Fade In. Nav dropdowns: Elementor's default is fine (fades at the trigger). |
| Shadows are semi-transparent and soft, never solid borders pretending to be depth. | Box Shadow: y 4–12, blur 16–32, spread 0, colour = ink at 6–12 % alpha. Never a 0-blur offset shadow. (Craft floor already says this; same rule.) |
| Tooltips: delay the first, instant thereafter. | Not natively controllable in Elementor; don't use tooltip widgets on marketing pages. |
| Asymmetric timing: slow where the user decides, fast where the system responds. | Accordion open 0.25 s, close 0.15 s if the control allows; otherwise one value ≤ 0.25 s. |
| Review your work the next day; play it slow. | Stage 7 happens after the push + 25 s, and Stage 12 is the next-day review in formal form. |

## C. Mobile platform floor (mobile-native)

These are the "it's a website in a browser" tells. Each is one declaration. Elementor can set some natively; the rest live in the kit mu-plugin's **mobile baseline** block. Ruling (CONFLICTS #9): the block is a **per-site Gate B item** — proposed in every Gate A message's Gate B list and approved site by site, never assumed. Until it is approved on a site, hover stays colour/opacity/shadow only (CONFLICTS #10).

| Tell | Fix | Where it lives |
|---|---|---|
| Hover state stuck after a tap | All `:hover` gated behind `@media (hover: hover) and (pointer: fine)` | Elementor can't gate hover by capability. **Mitigation without CSS:** keep hover changes to colour/shadow only (a stuck colour is invisible; a stuck 1.1 scale is not). Full fix: mu-plugin baseline wraps Elementor's hover classes — only if Adam approves the block. |
| Grey/blue flash on tap | `-webkit-tap-highlight-color: transparent` on `html` | mu-plugin baseline |
| Hero height wrong on phones | `100svh` for heroes, never `100vh`; `dvh` only for app shells | Container > Min Height: use **px or `svh`** (Elementor's unit picker includes vh/svh in 3.2x+/4.x) — set `svh`, never `vh`. |
| Page zooms into an input | Inputs ≥ 16 px | Form widget > Style > Field > Typography size **16 px minimum** at every breakpoint. FormCraft: field font size 16 in the spec. `audit_contact.py` to flag forms < 16 px (lesson: add check). |
| Tap feels laggy | `touch-action: manipulation` on buttons/links | mu-plugin baseline |
| Pull-to-refresh hijacks scroll | `overscroll-behavior: none` | **Not applied** — a marketing site is a scrolling document; pull-to-refresh is welcome. |
| Content under the notch | `viewport-fit=cover` + safe-area padding on fixed bars | Only if a sticky bottom call bar is used (PPC pages): mu-plugin adds the meta + padding for that one element. Otherwise skip. |
| Long-press selects button text | `user-select: none` on controls only, never body | mu-plugin baseline (buttons, nav items, tabs) |
| Carousel scrolls the page vertically | `touch-action: pan-y` on the track, or native scroll-snap | We don't ship carousels by default; if a Gate B carousel is approved, Elementor's Swiper sets this already. |
| Status bar colour mismatched | `theme-color` meta per colour scheme | mu-plugin: `theme-color` = the header background from `spec/site.json`. |
| Right in Chrome, wrong on the phone | Test on hardware | Stage 7 contact sweep is done on Adam's phone, not emulation, for at least the home page and the contact page. |

**Never ship:** `user-scalable=no` / `maximum-scale=1` (fix the input size instead); ungated hover scale; `100vh` heroes; `user-select: none` on body.

## D. Worst-case content pass (break-ui)

Demo data is chosen to make a design look good. Client data isn't. At Stage 3 the design agent records the **content extremes** for each page from the real site/brief, and at Stage 5 the QA agent renders them. Plausible or schema-backed, never random; one dataset carrying every extreme at once; report before fixing.

Elementor-site extremes to test (pick from the catalogue what the page actually has):

| Field | Worst case to render | What usually breaks |
|---|---|---|
| Nav item | Longest real service name (`Commercial Property Finance & Bridging`) + 7 items | Header wraps at ~1180 px; mobile menu label clipped |
| H1 | Longest real headline at 390 px | Orphaned word, three-line hero, button below the fold |
| Icon Box / card title | Longest service title, and one two-word title in the same row | Uneven card heights, orphan line; `align-items` issue |
| Card body | 2,000-char pasted description vs 20-char one | Cards of wildly different heights; clamp decision needed |
| Testimonial | A 90-word quote and a one-sentence quote; a name like `Aleksandra Wiśniewska-Kowalczyk`; a missing avatar | Quote mark alignment, name wrap, broken image icon |
| Phone / email | `+44 (0)151 000 0000 ext. 12` and a long email in the footer | Footer column overflow; `tel:` href wrong |
| Blog grid | 0 posts, 1 post, 13 posts | Empty-state gap; orphan card; pagination |
| Post title | 80-char title in the grid and the single template | Two-line clamp missing; related-posts row heights |
| Counter / stats | `0`, `1`, `1284`, `12,345,678` | "1 clients"; no thousands separator; badge width |
| Logo strip | 5 logos of wildly different aspect ratios | Row height jumps; one logo dominates |
| Legal page | The real privacy notice (138 blocks) | List nesting, italics, table cells — parity check |
| Address | A three-line address with a long town name | Footer/contact card wrap |

Report format (Stage 5 result): Broken / Ugly / Fragile per item, worst first, with the fix location (which helper or Style-tab control) and the decision where there is one (truncate vs wrap vs clamp, per field — never truncate numbers, dates or amounts).

## E. Feel (apple-design, one line)

Respond on press, not release; continuous feedback during an interaction; soft boundaries, not walls. On a marketing site this reduces to: short hover transitions, visible pressed states, no scroll-jacking, nothing that fights the thumb.
