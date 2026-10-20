# Rule conflicts across the design sources — for Adam to rule on

Sources: **Ours** (SKILL.md + PLAYBOOK.md), **Emil** (`references/emil-rules.md`), **Impeccable** (`references/impeccable-rules.md`), **taste** (`references/taste-rules.md`), **avoid-ai-design** (`tools/avoid-ai-design`), **Atlassian** (spacing scale), **UI UX Pro Max**.

Each item: the positions, my recommendation, and a `Decision:` line. Until a line is filled in, the recommendation is what the agents follow. Once filled in, the ruling is copied into the skill's Design Standards and this file keeps the history.

---

## 1. Motion duration ceiling

- **Ours:** no motion by default (performance rule 6); hover transitions only.
- **Emil:** UI motion < 300 ms; buttons 100–160, dropdowns 150–250, modals 200–500 ms. Never ease-in. Never scale from 0.
- **Impeccable:** micro 100–150, standard 150–300, "focal" entrances 300–500, and up to 500–800 ms for one hero moment.
- **taste:** MOTION_INTENSITY dial; baseline 6, trust-first 2–3.

Real disagreement: Impeccable's 500–800 ms hero entrance versus Emil's hard 300 ms UI ceiling versus our "none".

**Recommendation:** Ours stays the default (no entrance animations; hover 0.15–0.2 s per Emil). When a brief asks for motion, Emil's numbers govern everything interactive (menus, buttons, accordions, popups) and Impeccable's 300–500 band is allowed **only** for one first-view hero element, never 800 ms, and only via Elementor's native Fade (no Zoom/Bounce). Dial written in the spec header.

Decision: ______

## 2. Eyebrow labels

- **Ours / Impeccable:** eyebrow is a hard ban (craft floor, refuse-by-default; Gate B to use one).
- **avoid-ai-design:** all-caps mono eyebrow is SD tell; "01/02/03" number eyebrows are a tell.
- **taste:** allowed, max one per three sections.

**Recommendation:** keep the hard ban on redesign/new pages; clone pages reproduce whatever the reference has. taste's "1 in 3" is not adopted.

Decision: ______

## 3. Centred hero

- **Ours:** clone pages copy the reference; redesign/new pages follow the Direction in the spec.
- **avoid-ai-design L1:** "centred hero over three icon cards" is a layout tell.
- **taste:** hero must not be centred when DESIGN_VARIANCE > 4; may be centred at ≤ 4 (trust-first clients).
- **Impeccable:** the brief wins; the Persuade "opening test" (does the first viewport make the claim and the proof?) matters more than alignment.

**Recommendation:** adopt taste's rule as a Gate A check for redesign/new: a centred hero is allowed only if the spec sets variance ≤ 4 and says why (trust-first client). Clone pages exempt.

Decision: ______

## 4. Three equal feature cards

- **taste:** banned on any page it designs.
- **avoid-ai-design L1/L2:** a tell when combined with a centred hero or tinted icon chips.
- **Ours:** clone fidelity — if the reference has three cards, we build three cards.

**Recommendation:** clone pages keep the reference's 3-up (reported as advice at Gate A). Redesign/new pages avoid 3 equal cards unless the content is literally three parallel things (three service tiers, three locations) — then allowed with a note in the spec.

Decision: ______

## 5. Dark mode

- **taste:** mandatory for consumer pages.
- **Impeccable:** light or dark is forced by the scene/brief, never both by default.
- **Ours:** Elementor has no native colour-scheme switch; a dark mode means custom CSS plus a second set of globals, which is Gate B territory and a maintenance cost for the client.

**Recommendation:** do not adopt. One theme per site, chosen in the Direction. Dark mode only if a client asks, as a Gate B item.

Decision: ______

## 6. Serif typefaces

- **taste:** serif very discouraged as default; Fraunces and Instrument Serif banned.
- **Impeccable:** avoid the "default faces" list (Inter, Roboto, Playfair, Fraunces, Instrument Serif…); pick from the brief's subject.
- **avoid-ai-design:** "broadsheet cosplay" (serif + rules + small caps) is SD3.
- **Ours:** reference's fonts on clone; Design Standards on redesign/new; performance rule caps weights.

**Recommendation:** no ban on serifs; ban on the *default* serifs (Fraunces, Instrument Serif, Playfair as a display default). A serif needs a reason in the Direction line. Clone pages keep the reference's face (replaced only for performance at Gate B, per existing rule).

Decision: ______

## 7. Em-dashes in copy

- **taste:** completely banned.
- **Ours:** no rule.

**Recommendation:** adopt for copy we write (redesign/new and any new copy on clone pages). Clone pages reproduce the reference's text as-is. Add an em-dash check to `audit_contact.py` so it's mechanical.

Decision: ______

## 8. Body measure

- **Ours (craft floor):** 65–75 characters.
- **Impeccable:** 45–75 characters.

**Recommendation:** widen to 45–75 to match Impeccable; 45–60 for narrow columns beside an image, 60–75 for single-column text. Not a real disagreement, ours was just the narrow end.

Decision: ______

## 9. Mobile platform CSS (Emil's mobile-native) vs no-custom-CSS rule

- **Emil:** `-webkit-tap-highlight-color: transparent`, `touch-action: manipulation` on controls, `user-select: none` on buttons, `100svh` heroes, 16 px minimum on inputs (stops iOS zoom), `theme-color` meta. Several of these are impossible from the Elementor Style tab.
- **Ours:** no custom CSS without approval (rule 3).

**Recommendation:** a one-time, pre-approved "mobile baseline" block (about 12 lines) in `deploy/mu-plugins/ignite-site-fixes.php`, identical on every site, versioned in the kit. Everything else stays native: inputs at 16 px via the Form widget's typography, hero min-height via the container control. Needs your one-time approval so it stops being a per-site Gate B item.

Decision: ______

## 10. Hover effects on touch devices

- **Emil:** hover effects must be gated behind `@media (hover: hover)` so phones don't get stuck hover states.
- **Ours:** Elementor applies hover styles unconditionally.

**Recommendation:** keep hover to colour, opacity and shadow only (a stuck hover of those is invisible); no hover transforms or "Grow/Float" effects on anything tappable. If a hover transform is wanted, it goes behind the mobile baseline block's `(hover: hover)` guard (depends on item 9).

Decision: ______

## 11. Design dials and Design Read / Visitor mode header lines

- **taste:** three dials (variance/motion/density) + Design Read.
- **Impeccable:** `Visitor mode: Persuade | Read | Operate | Experience`.
- **Ours:** `Direction:` line only.

Not a conflict, a merge: all three become lines in the spec header (Phase 2 format), filled at Stage 2/3, read by design and QA. Cost is three lines per site.

**Recommendation:** adopt.

Decision: ______

## 12. Section-family-used-once and zigzag cap

- **taste:** each layout family once per page; zigzag ≤ 2.
- **avoid-ai-design L9:** cookie-cutter section order is a tell.
- **Ours:** no rule; long service pages often repeat a zigzag 4–6 times.

**Recommendation:** adopt as a Gate A *note*, not a block: the spec lists the family per section; the design agent must justify a repeat in one sentence. Clone pages exempt.

Decision: ______

## 13. Worst-case content pass (Emil's break-ui)

- **Emil:** test every component with the longest/shortest/empty/odd content before shipping.
- **Ours:** `audit_widths.py` and the five-breakpoint render, but with real content only.

Not a conflict; an addition. **Recommendation:** Stage 5 gets a worst-case pass on nav (longest label + one extra item), H1 (longest service name), cards (one card with double the copy), testimonials (a 60-word quote), phone/email (the longest the client could have), counters (6-digit numbers). Reported as Broken / Ugly / Fragile, Broken must be fixed before push.

Decision: ______

## 14. Spacing scale vs Impeccable's "arbitrary spacing" detector

- **Atlassian:** 8-based scale (4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96…).
- **Impeccable:** flags any spacing not on a consistent scale; indifferent to which scale.
- **UI UX Pro Max:** proposes its own spacing per design system.

No conflict in practice: Atlassian is the scale, the Impeccable detector verifies it, UI UX Pro Max's suggestions get snapped to it (existing "snaps > 4 px are reported at Gate A" rule). Nothing to decide.

## 15. Where "taste" sits versus "the brief wins"

- **Impeccable / Ours:** the brief wins, even when it asks for an SD look.
- **taste / avoid-ai-design:** bans are absolute.

**Recommendation:** the brief wins, always, as now. A banned pattern the client asked for is built, noted at Gate A as advice once, and marked `ignore` in the spec so it isn't re-raised. The bans are there to catch *our* defaults, not the client's choices.

Decision: ______
