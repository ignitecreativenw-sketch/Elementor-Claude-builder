# Impeccable's rules, translated for Elementor builds

Source: github.com/pbakaus/impeccable @ 83c2c73 (v4.3.x, Apache 2.0). Fetched at Stage 1 into `tools/impeccable/`. Impeccable is a 24-command design-direction system for code-first frontends with its own launcher, detector hook, decision pages and image-generated comps. Most of that machinery assumes React/CSS and a dev server; what transfers to a native-Elementor build is its **craft floor**, its **four visitor modes**, its **direction discipline** (new-work), and the per-topic rules in `typeset`, `layout`, `colorize`, `animate`, `adapt` and `polish`. This file is that subset, each rule mapped to where it lives in our pipeline. The detector (`impeccable detect`) remains an optional Stage 7 pass when the binary downloads.

---

## A. Visitor mode (decides what "good" means on the page)

Impeccable names what the visitor's success looks like, and the mode changes the rules that follow. Choose it per surface, not per product, and write it into the spec header.

| Mode | Surface | What outranks what |
|---|---|---|
| **Persuade** | Home, service pages, landing/PPC, pricing | Attention and action. The opening makes the offer intelligible, exposes one clear action, and demonstrates something only this client can prove. Composition may be asymmetric or disruptive if the world earns it. Bolder colour strategies allowed. |
| **Read** | Blog index, single post, guides, legal | Comprehension and wayfinding. Stable structure, 45–75 ch measure, predictable density. A fashion house's docs are still Read. |
| **Operate** | Contact forms, booking, client portals | Scanability, native expectations, consistency. Brand lives in precise details, not expression. |
| **Experience** | Portfolio, gallery, case-study showcase | The work leads from the first viewport; the interface recedes. |

Our mapping: every `spec/<page>.md` carries `Visitor mode:` on the line after `Mode:`. Clone pages inherit the reference's mode; redesign/new pages have it chosen by the design agent and shown at Gate A.

## B. Direction discipline (new-work) — for `redesign` and `new` pages only

| Rule | Our implementation |
|---|---|
| **Decide what is already true first.** A missing DESIGN.md doesn't make a project greenfield; the reference, brand guidelines, existing site, and client's own artefacts are evidence. | `spec/site.json` tokens + `reference/design-tokens.json` are the incumbent world. Clone pages never get a new world. |
| **Three amounts of invention:** extend a surface (inherit everything, resolve only the new content); create a whole surface inside an established world (keep the system, derive 5–7 structures from the content and task); create or replace the world (name the mechanism, the audience's real scene, its cultural home; list seven concrete systems/artefacts/places the audience knows, spanning at least three material families; keep the category's obvious page and its predictable opposite out of the list). | `mode: new` inside an existing site = "whole surface inside an established world": structure options only, identity fixed. `mode: redesign` of the whole site = "replace the world": the seven-candidate derivation is done in the spec's `Direction` block, and one direction plus one or two alternatives goes to Gate A. We don't run Impeccable's dice/decision-page machinery; Gate A is the decision page and Adam is the roll. |
| **The rut is named before the list.** The page this category always ships, and its predictable opposite, are excluded from the candidates. The brief's literal reading (a bakery → bread photo) gets at most one slot. | Design agent writes the rut in one line in the spec before the candidates. |
| **Colour strategy before colours:** Restrained (neutrals + one accent; default for Operate/Read), Committed (one saturated colour carries 30–60 % of the surface), Full palette (3–4 named roles), Drenched (the surface is the colour). Colour commits at page scale — regions, not scattered accents. Light or dark is forced by a one-sentence physical scene (who, where, what light), never defaulted. | `Direction` block names the strategy. Persuade pages may take Committed or Full; Read/Operate default Restrained. |
| **Faces like objects from the subject's world.** The named training-data defaults (Fraunces, Playfair, Cormorant, Lora, Crimson, Newsreader, Syne, Space Grotesk, Space Mono, IBM Plex, Inter-as-display, DM Sans/Serif, Outfit, Plus Jakarta, Instrument Sans) need a reason no other face satisfies; "books want a serif" is not a reason. | Design agent lists the face and the reason; Gate A shows both. Two families, four weights max (our perf rule) still binds. |
| **Calibration against the clusters:** warm cream + serif display + terracotta; near-black + neon + glow edges; broadsheet hairlines + italic serif + tracked mono. All legitimate when the brief asks; landing there when the brief is free means the self-check failed. Warm/bookish/family/child subjects come out cream by reflex: treat that first palette as already spent. | Same clusters as avoid-ai-design SD1–SD3/SD5; one check, run once, at Gate A. |
| **Truth binds claims, not demonstrations.** Synthetic illustrative content is fine at full fidelity if labelled; prices, customers, benchmarks, capabilities are never invented. | Our `[CLIENT TO CONFIRM]` + banner rule; regulated-client copy rule. |
| **Persuade opening test:** offer intelligible, one visible primary action, a legible reading order. A committed form that hides the offer has not finished translating. | Stage 5 silhouette test + a "what is the offer, what is the action" one-liner per hero in the QA result. |

## C. Craft floor (verified every build, same screenshot round as the diff)

Already folded into the skill's Craft floor section; restated here with the Elementor control.

| Check | Value | Elementor control |
|---|---|---|
| Contrast | body ≥ 4.5:1, large ≥ 3:1, controls/icons/focus ≥ 3:1; secondary text on a coloured surface tinted from that hue, never grey | Global colours: a `Text on primary` and `Muted on primary` role, not grey |
| Depth | shadows carry offset + soft blur; zero-offset halo is decoration | Style > Box Shadow: y 4–12, blur 16–32, ink at 6–12 % |
| Spacing | tight groups, generous separation, more above a heading than below; read computed values | SP tokens; Heading margin-top > margin-bottom via container gap |
| Type | measure 65–75 ch (Impeccable: 45–75), display ≤ 6 rem, tracking floor −0.04 em, balanced headings, obvious scale and weight steps; run the real copy at every breakpoint | Text Editor max-width; Heading letter-spacing ≥ −0.04 em; worst-case copy pass (emil D) |
| Motion | one authored moment, not scattered effects; exponential ease-out from a visible default; blur/clip/mask allowed when smooth | Our default: none; if earned, one hover language + one entrance (Gate B) |
| States | hover, disabled, loading, error, empty; real content; keyboard focus | Form widget error/success styles; button hover; Posts widget "no results" text |
| Browser surfaces | selection colour, caret, scrollbar, focus ring, underline offset, tabular numerals | Site Settings > Typography/Links/Focus; counters with tabular figures |
| Copy | controls name their action; errors name the problem and the recovery | Button labels verbs; Form messages written, not default |
| Coverage | every brief requirement present and findable in seconds | Spec checklist at Stage 7 |

**Refuse by default** (brief can earn any back except the eyebrow): same-size icon+heading+text cards as the page skeleton; hero-metric template; **kicker/eyebrow above a heading (a ban, never earned back)**; section numbers 01/02/03 unless they carry information; modal for a task that needs no interruption; gradient text; glass/blur as decoration; coloured left/right border > 1 px on cards; hard zero-blur offset shadows; sparklines/rings as content; monospace as costume; system display face as the headline voice; unicode/emoji as icons; geometric masks faking organic cut-outs; light/dark picked by category.

## D. Typography (typeset)

| Rule | Elementor |
|---|---|
| Fewest roles and families that make hierarchy unmistakable; combine size, weight, space and tone — don't ask size alone to do the work | Site Settings > Typography: H1–H4, body, small, label roles; two families |
| Body floor 16 px; prose 45–75 ch; line-height inversely with measure | Body 16–18 px, Text Editor max-width 640–720 px, lh 1.5–1.65 |
| Light text on dark: more leading, a touch more tracking, one step more weight | Hero on navy/dark: lh +0.05, letter-spacing +0.01 em, weight 500 → 600 |
| Load only used weights; metric-compatible fallbacks; no invisible text | mu-plugin font trimming; `font-display: swap` |
| Paragraph rhythm by spacing OR indent, never both | Text Editor paragraph spacing via gap; no text-indent |
| Preserve zoom and user font settings | Never `maximum-scale`; px sizes are fine in Elementor since zoom scales them |

## E. Layout

Squint test (primary, secondary, groups legible with detail blurred); group by meaning before adding containers; rhythm from deliberate contrast between tight and generous; documented spacing scale, with a 4-unit base for the middle steps an 8-only scale misses; hierarchy from product priority not framework defaults; `gap` for sibling rhythm; depth only when it clarifies; optical corrections only after inspecting the render. Verification is per claim with rendered evidence, never a bare yes.

Mapped: Atlassian scale already has the 4-unit middle steps (2/4/6/12/20). Squint test runs with the silhouette test at Stage 5.

## F. Colour (colorize)

Roles not swatches (canvas, elevated surface, primary/secondary text, action, focus, selection, borders, semantic, data); strongest colour owns a region; primary action is easy to find and its colour isn't spent on decoration; tint neutrals only when the brand hue creates cohesion; secondary text on coloured surfaces derived from the surface/foreground hue; dark mode composed, never inverted; OKLCH for new palettes; verify computed pairs in all states, both themes; colour never the only code.

Mapped: Elementor Global Colours are the role tokens — name them by role (`Canvas`, `Surface`, `Ink`, `Ink muted`, `Action`, `Action hover`, `Line`, `On action`), never by hue.

## G. Motion (animate)

Find the job first (acknowledge, make state legible, continuity, direct attention, embody the world); write the thesis (focal moment, continuity, feedback, budget); a generic fade-and-rise, hover lift, parallax or scroll reveal is not a thesis. Durations: 100–150 feedback, 150–300 routine state, 300–500 overlay/view transition, 500–800 one authored focal entrance. Exit faster than entrance. `cubic-bezier(0.16, 1, 0.3, 1)` for arrivals; no bounce/elastic by reflex. Only transform/opacity for layout-affecting motion; bound blur/filter to regions; `will-change` only during animation. Reduced-motion path keeps opacity/colour/state feedback.

Mapped: identical to emil A except the upper band (500–800 ms focal entrance) which Emil would cap at 300 for UI — see CONFLICTS.

## H. Adapt (responsive)

Mobile: single column, full-width components, 44×44 touch targets, bottom sheets over dropdowns, progressive disclosure, 16 px minimum text, thumb-reach controls, sticky header for context. Tablet: two columns, master-detail, orientation-aware. Verify on real devices, both orientations, Safari and Chrome, 320 px and 4K, throttled network; for any gesture control, tap it, drag it, and scroll across it, and say which engine/device produced the evidence.

Mapped: our Responsive Rules already encode the column collapse and 44 px targets; "scroll across the control" and "name the engine" go into the Stage 7 QA result format.

## I. Polish (refine, never redesign)

Classify every drift before fixing: missing token / one-off implementation / conceptual mismatch / local defect; fix at the narrowest correct level; use the feature yourself at representative sizes with the real content lengths; a detector result is defect evidence, not proof of quality.

Mapped: this is our "fix in the shared helper, not the page" rule with a vocabulary for the retro's lessons table (Kit = missing token/one-off; Playbook = conceptual mismatch; Skill = standard).

## J. Verification posture (every Impeccable command ends the same way)

Verify in bounded passes, not a loop: build fully, inspect once with a batched round (desktop and mobile together), fix everything it shows in one batch, confirm with at most one more round, stop. Open-ended self-QA burns the user's money doing worse what the finish hand-offs do better. Answer each verification item with rendered or source evidence, never a bare "yes".

Mapped: our two-round cap at Stage 7 is this rule; the "evidence per item" requirement goes into the QA agent's result format.
