# taste-skill rules, translated for Elementor builds

Source: github.com/leonxlnx/taste-skill @ d237dd3 (Oct 2026). Fetched at Stage 1 into `tools/taste-skill/`. taste-skill is a front-end "taste" guard: it infers a brief, sets three dials, then enforces a long list of bans aimed at the look every AI page converges on. Most of its rules are about **`redesign` and `new` pages**; a `clone` page follows its reference and only takes the hygiene rules (copy, accessibility, nav sanity). Sections 0, 1, 4, 5.D, 6, 9, 11 and 14 of its SKILL.md are what this file distils.

---

## A. Design Read (brief inference, Stage 2 → spec header)

Before the spec, write one line that answers: who lands on this page, what they came to do, and how much trust they need before they act. taste calls this the Design Read. It sits next to Impeccable's `Visitor mode:` line in the spec header:

```
Design Read: <who> arriving from <where>, wants <action>; trust needed: <low|medium|high>
Visitor mode: Persuade | Read | Operate | Experience
Dials: variance <0–10> · motion <0–10> · density <0–10>
```

## B. The three dials (set once per site, in the spec header)

| Dial | Meaning | taste baseline | Trust-first / regulated (finance, legal, medical, trades with compliance) |
|---|---|---|---|
| DESIGN_VARIANCE | how far from the safe centred layout the page may stray | 8 | 3–4 |
| MOTION_INTENSITY | how much motion is allowed at all | 6 | 2–3 |
| VISUAL_DENSITY | how much goes on screen per viewport | 4 | 4–5 |

For our work the dials are a **spec input, not a default**: our performance rule (no motion by default) already caps motion at ~2 unless Adam asks for more, and clone pages inherit their reference's variance. Write the three numbers in the spec header so the design and QA agents judge the same page by the same dials.

## C. Type and colour bans (redesign/new)

| Rule | Elementor implementation |
|---|---|
| Serif as the default body or display face is very discouraged; Fraunces and Instrument Serif are banned outright (the AI-default serif). | **Stricter ruling** (CONFLICTS #6): sans-serif only on redesign/new; a serif only when the client's existing brand already uses one. |
| One accent colour maximum; accent saturation under 80 %. | Global Colours: Primary (accent) is the only saturated colour; Secondary/Text/Accent slots hold neutrals and tints. Check the HSL of Primary. |
| The "premium consumer" palette (beige/cream ground + brass/gold accent) is banned as a default. | Same ban as avoid-ai-design SD1 (cream + terracotta). Only if the brief names it. |
| Shape lock: one corner-radius family per site; colour lock: no new colour introduced per section; theme lock: one light or dark theme per page, no section-by-section flipping unless the spec calls the dark band. | Radius set once in Global Styles / `layout.py` tokens; every container/card reads the token. Dark bands are listed in the spec, not improvised. |

## D. Hero rules (redesign/new)

| Rule | Elementor implementation |
|---|---|
| Headline ≤ 2 lines at desktop; sub-text ≤ 20 words; ≤ 4 text elements in the hero in total (eyebrow counts). | Heading widget size chosen so the H1 wraps to 2 lines at 1440 and 3 at 390; the copy agent trims to the word count. |
| Headline size ≤ 6 rem (96 px). | Heading > Typography: desktop ≤ 96 px, usually 48–72. |
| No trust strip (logos / "as seen in" / star rating row) inside the hero container. | Trust strip is its own section below the hero, if it exists at all. |
| Anti-centre: when DESIGN_VARIANCE > 4 the hero is **not** a centred headline over a centred button. Left-aligned, split or asymmetric. | **Not adopted** (CONFLICTS #3): no rule on hero alignment; the design agent decides. |

## E. Section and layout bans (redesign/new)

| Rule | Elementor implementation |
|---|---|
| Nav on a single line, ≤ 80 px tall, no stacked utility bar + main bar. | Header template: one container, height ≤ 80; the phone number goes in the nav row, not above it. |
| Eyebrow (small all-caps label above a heading): at most one per three sections. | **Adopted** (CONFLICTS #2): max one per three sections on redesign/new, no all-caps mono, no numbering. |
| Split header ban: no "half heading left, half paragraph right" section opener. | Section headings stack: heading, then intro, same column. |
| Zigzag (image-left/text-right alternating) rows: maximum 2 per page. | **Hard rule** (CONFLICTS #12). `layout.py` `row()` alternation stops at two; the third feature uses a different family. |
| Each section-layout family (cards grid, zigzag, stat strip, testimonial slider, FAQ accordion, CTA band) is used **once** per page. | **Hard rule** (CONFLICTS #12): spec lists the family per section; a duplicate sends the spec back before Gate A. |
| No "three equal feature cards" row (the AI default). Use 2, 4, a 2+1 split, or a list. | Icon Box / Image Box grids avoid 3-up on redesign/new. Clone pages keep the reference's 3-up. |
| Bento grids need a deliberate cell count and ≥ 2 cell sizes; no uniform tiles called a bento. | Nested containers with explicit widths; if every cell is equal, it's a grid — call it that. |
| No scroll cues ("scroll ↓" arrows/bouncing chevrons), locale/timezone strips, section-number eyebrows (01/02/03), decorative dots, version labels ("v2.0"), pills/badges laid over photos, photo-credit captions. | None of these widgets are added. Overlaps with avoid-ai-design SD5/SD6. |
| Testimonial quotes ≤ 3 lines; name + role, no star-row unless real. | Testimonial widget copy trimmed; Star Rating widget only with a real review source. |

## F. Copy bans (all modes, including clone when we write new copy)

| Rule | Note |
|---|---|
| Em-dash completely banned in page copy. | Use a comma, a full stop, or a colon. (Clone pages keep the reference's punctuation; copy we write never uses one.) |
| No "Welcome to", no "In today's fast-paced world", no "Unlock", "Elevate", "Seamless", "Empower". | Overlaps our own copy rule. |
| Headlines state a specific benefit or a specific thing, not a category ("Expert mortgage advice" ✗ / "Mortgages for the self-employed, agreed in principle in 24 hours" ✓). | Copy agent. |

## G. Dark mode and reduced motion

| taste rule | Elementor reality |
|---|---|
| Dark mode is mandatory for consumer-facing pages. | **Not adopted** (CONFLICTS #5): one theme per site; dark mode only on a client's request, Gate B. |
| `prefers-reduced-motion` handling is mandatory when MOTION_INTENSITY > 3. | Elementor Pro 4.x honours reduced-motion for its own entrance animations; with our no-motion default this is moot. If Adam allows motion > 3 on a site, it becomes a mu-plugin "mobile baseline" item (see emil-rules C). |

## H. Redesign protocol (`mode: redesign`)

taste's rule for modernising an existing site matches ours and tightens it:

- Preserve: information architecture, URL slugs, nav labels, form field names and IDs, phone numbers, the order of pages. (Our `audit_contact.py` already guards the contact facts.)
- Modernisation levers, applied in this order and stopping when the page reads as current: type scale and spacing → colour discipline (one accent) → hero → section families → motion. Never start with motion.
- The redesign must still be recognisable to a returning customer. If the client's own staff wouldn't know it was their site, the lever went too far.

## I. Pre-flight checklist (taste §14, merged into `qa/design-checklist.md`)

Before Gate A on redesign/new pages, tick: Design Read written · dials set · one accent, saturation < 80 % · no banned serif · hero ≤ 4 text elements, headline ≤ 2 lines, ≤ 6 rem · no trust strip in hero · nav single line ≤ 80 px · no split headers · zigzag ≤ 2 · no section family used twice · no 3 equal cards · no scroll cues / locale strips / number eyebrows / decorative dots / version labels / badge-on-photo / photo credits · quotes ≤ 3 lines · no em-dashes in copy we wrote · variance > 4 → hero not centred.

---

What we do **not** take from taste-skill: its React/Tailwind component recipes, its default-to-dark-mode rule, its anti-centre hero rule, its "variance 8" default (ours is set per site by the brief), and its animation library guidance.
