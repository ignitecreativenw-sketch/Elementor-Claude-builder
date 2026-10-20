# Elementor Clone Build — Playbook

Follow this in order for every site. Each stage has an entry condition, the steps, and an exit condition. Do not start a stage until the previous one's exit condition is met. Where a step says **STOP**, wait for Adam. Everything else runs to completion without asking.

The skill (`skills/elementor-clone-build/SKILL.md`) holds the standards and the why; this playbook is the order of operations and the checks. If they ever disagree, the playbook wins on sequence and the skill wins on standards.

---

## The team — which agent runs which stage

One orchestrator holds this playbook and the gates; seven specialists each carry one slice of the skill and one or two stages. Briefs are in `agents/`; Claude Code definitions in `.claude/agents/` (prefixed `ecb-`). The spec files are the shared memory — agents hand off through the project folder, never through each other's context. Full table, parallelism map, hand-off contract and model tiers: `agents/README.md`.

| Stage | Agent | Parallel? |
|---|---|---|
| 0 Intake, Gate A message, 10 Handover, 12 Retro | orchestrator | no |
| 1 Site setup | deploy | no |
| 2 Capture | capture | per page |
| 3 Spec + direction | design | page one alone, then per page |
| 4 Build | build | per page |
| 5 Local QA | qa | per page |
| 6 Push | deploy | no (one site) |
| 7 Staging QA | qa | per page |
| 8 SEO | seo | alongside 9 |
| 9 Performance | perf | alongside 8 |

Every agent returns the hand-off block (STAGE / STATUS / WROTE / CHECKS / GATE B ITEMS / LESSONS / NEXT), under 300 words, paths not contents. The orchestrator copies LESSONS into the build report's Gotchas so Stage 12 finds them. Judgement stages (design, Gate A, Stage 7 visual, Stage 12) run on the strongest model; mechanical stages run mid-tier; nothing runs small without a spec to follow and an auditor to catch it.

---

## Stage 0 — Intake (one message, all questions at once)

**Entry:** Adam has given a reference (URL or PDF) and a target site.

1. Copy the kit (`My Drive/WEBSITE BUILDER STORAGE/Elementor-Claude-builder`) to `WEBSITE BUILDER STORAGE/<Client>` if the folder doesn't exist. Everything lives in that Google Drive folder; connect it to the session. Keys and `deploy/.env` stay outside Drive (`WEBSITE_CORE_HOME` on the Mac, or the client's Claude Project).
2. Ask for everything missing in a single message:
   - pages in scope; header/footer in or out
   - staging URL; the site's **Website Core** "Copy for AI" block (site URL, endpoint, write key — Adam installs the plugin and creates the key in Tools › Website Core; the key is rotated on first use and may be kept in the client's Claude Project so later chats reuse it, see `references/website-core.md`); SFTP/FTP for the mu-plugin only
   - one exported Elementor template JSON from the target site (schema ground truth)
   - SEO plugin; target keywords, location, business type; regulated industry yes/no
   - brand tokens if they exist
   - **contact details:** phone (display + E.164), email, form recipient, address
   - **host profile:** nginx/Apache, SSH yes/no, cache layer, bot protection, mail route
   - any pages that are `new` (no reference) and any that are `redesign` rather than `clone`
3. Read `LESSONS.md` in the kit before asking anything — a previous build may already answer it or add a question.
4. Write `spec/site.json` from the answers. Adam writes `deploy/.env` himself (never paste credentials into chat).

**Exit:** `spec/site.json` has no placeholders; `deploy/.env` exists on the Mac; `python3 deploy/push_core.py --rotate` has been run once with the pasted key, `--action status` answers and `reference/status.json` exists. Website Core is the only route; there is no fallback to choose.

**STOP if:** contact details are unknown. Build nothing until they exist.

---

## Stage 1 — Site setup (once per site, before any page)

**Entry:** Stage 0 exit.

0. `python3 deploy/push_core.py --action '{"action":"sample","id":<page or template id from status>}'` → `reference/sample-<id>.json` is the schema ground truth for step 7 (containers vs sections, settings keys, `version`, `__globals__`). Sample the kit id too before step 1.
1. Elementor globals from the tokens: colours, fonts, heading typography, button style, container width, default gap `space.500`, link/selection/focus colours. One `kit` action (merged; `system_colors`, `system_typography`, `container_width`). Site title/tagline/permalinks/timezone/icon: `settings`.
2. Breakpoints: `python3 deploy/set_breakpoints.py --apply` (Mobile Landscape ≤880 on).
3. Performance flags on: Google Fonts local; Optimized Markup; Improved CSS loading; Improved Asset loading; Element caching; Inline font icons; Lazy-load backgrounds.
4. Element Manager: disable widgets the spec will not use.
5. Upload `deploy/mu-plugins/ignite-site-fixes.php` by SFTP/FTP (edit the two `PER SITE` lines first). Website Core cannot install code, so this is the one SFTP step; the Yoast-REST registration in it is unused (SEO rides on the `page` action).
6. Staging on `noindex` (`settings` with `search_visible: false`). Cache-lifetime headers set at the host panel/CDN if nginx.
7. Verify the sample export's `version`, id format and key names against `build/build_template.py`; adjust the generator if they differ.
8. Fetch the design tooling into `tools/` (gitignored): `git clone -q --depth 1 https://github.com/nextlevelbuilder/ui-ux-pro-max-skill tools/ui-ux-pro-max-skill` and `git clone -q https://github.com/funboy322/avoid-ai-design tools/avoid-ai-design && git -C tools/avoid-ai-design checkout 2b7c71836b06cdf6b3d73265b56490c1b75ad5aa`. Confirm `node --version` ≥ 18 for the scanner. Also `git clone -q https://github.com/emilkowalski/skills tools/emil-skills && git -C tools/emil-skills checkout 2d22863`, `git clone -q https://github.com/pbakaus/impeccable tools/impeccable && git -C tools/impeccable checkout 83c2c73` and `git clone -q https://github.com/leonxlnx/taste-skill tools/taste-skill && git -C tools/taste-skill checkout d237dd3`. The distilled, Elementor-mapped rules from each live in `references/emil-rules.md`, `references/impeccable-rules.md` and `references/taste-rules.md`; where they disagree, `references/CONFLICTS.md` records the ruling (the recommendation stands until Adam fills in a `Decision:` line).

**Exit:** all eight done and noted in `qa/build-report.md` under "Site setup".

---

## Stage 2 — Capture

**Entry:** Stage 1 exit.

1. URL: `python3 build/capture_reference.py <url>` for each page → `reference/` screenshots at 1440/1024/390, `design-tokens.json` per breakpoint with `spacing_snap`, `content.json`, `combined.css`.
2. PDF: `pdftoppm -r 150 -png`, `pdftotext -layout`, `pdffonts`; colours sampled with PIL; scale factor noted.
3. Legal/regulated pages: `build/extract_legal.py` → verbatim blocks; parity count recorded.
4. Images: `python3 build/download_assets.py` → `assets/` as WebP at rendered-width×2 (caps 1920/1200/800), `assets/manifest.json` with alt text.

**Exit:** tokens + content files exist for every page in scope. No screenshots opened unless a decision needed one.

---

## Stage 3 — Section Spec → **Gate A**

**Entry:** Stage 2 exit.

1. Write `spec/<page>.md` per page in the skill's format. Header carries `Mode: clone | redesign | new`, responsive source, and every spacing snap over 4 px.
2. Every reference pattern mapped to a native widget from the table. Anything unmapped → "Needs approval" list.
3. `mode: new` or gap-filling pages: run UI UX Pro Max `--design-system --density 3` and adopt only what the spec header needs.
2a. **Spec header lines (every site).** Write `Design Read:` (who lands, from where, wanting what, trust needed), `Visitor mode:` (Persuade / Read / Operate / Experience) and `Dials:` (variance · motion · density, per `references/taste-rules.md` B; motion defaults to 2) into the spec header. They are read by design and QA alike. Redesign/new specs are checked against the CONFLICTS.md rulings before Gate A: sans-serif only (#6), eyebrows ≤ 1 per 3 sections (#2), no 3-equal-card rows without a reason (#4), each layout family once and zigzag ≤ 2 (#12), one theme (#5); a spec that breaks one goes back to the design agent, it does not reach Adam.
3a. **Anti-AI-design review (every `redesign` and `new` page, and any section the reference leaves undecided) — `/avoid-ai-design`.** Before the spec is presented, check the planned direction against `tools/avoid-ai-design/references/ai-tells-catalog.md`, especially the second-order clusters SD1–SD8 (cream + terracotta, near-black + acid accent, broadsheet cosplay, template chrome, one accented headline word, decorative 01/02/03, fake window chrome, the purple-escape accent) and the layout tells L1–L9 (centred hero over three icon cards, generic stat strip, default four-column footer, cookie-cutter section order). For each part of the plan ask: *would I arrive here for any similar page?* If yes, revise it from the client's subject — trade, place, materials, the domain's own artefacts — and record what changed in the spec under `Direction`. UI UX Pro Max output is a proposal that frequently lands in an SD cluster; it goes through this check like anything else. Write the committed direction (4–6 named colours with roles, faces and roles, the layout idea in one sentence, the one signature detail) into the spec header; it is the site's single design contract — the Elementor globals and `layout.py` implement it, so page two cannot drift from page one (catalog X1). `mode: clone` pages are exempt: the reference wins, and any tells it carries are reported as advice at Gate A, not fixed.
4. Forms: default Elementor Pro Form; FormCraft only if logic/calculation/multi-step/popup is required, with `spec/forms/<name>.json`.
5. Write `qa/seo-checklist.md`, `qa/perf-checklist.md`, `qa/design-checklist.md` for the page.

**STOP — Gate A.** One message to Adam: spec summary, per-page mode, the committed direction and what the anti-AI review changed (with one or two alternatives in a sentence), deviations, spacing snaps > 4 px, designed-responsive sections, site-wide settings switched on in Stage 1, Gate B items (always including the mobile baseline CSS block from `references/emil-rules.md` C, proposed per site — CONFLICTS #9). Wait for "approved" or amendments.

**Exit:** Adam has approved the spec.

---

## Stage 4 — Build

**Entry:** Gate A approved.

1. `build/build_<page>.py` per page, importing `layout.py` and `build_template.py`. Shared sections (cards, process block, CTA, lender/logo strip) are functions used by every page that needs them.
2. Spacing via `SP[...]` tokens only. Responsive values at desktop/tablet/mobile (+ mobile_extra where the rules say so).
3. `python3 build/build_<page>.py` → `templates/<page>.json`.
4. FormCraft forms: `python3 build/build_form.py spec/forms/<name>.json` → `templates/forms/<name>.txt`.

**Exit:** every in-scope page has a template. No literal px in padding/margin/gap. No placeholder tokens.

---

## Stage 5 — Local QA (before anything touches staging)

**Entry:** Stage 4 exit.

1. `python3 build/audit_widths.py` → must pass.
2. `python3 build/audit_contact.py` → must pass.
3. `python3 build/render_preview.py templates/<page>.json 1440 > qa/preview/<page>.html` (repeat for 1024 and 390 if layout differs) → review in the browser pane at 1440/1024/880/768/390.
2b. **Worst-case content pass** (`references/emil-rules.md` D): re-render with the longest nav label plus one extra item, the longest H1, one card with double copy, a 60-word testimonial, the longest phone/email, 6-digit counters. Report Broken / Ugly / Fragile in `qa/design-checklist.md`; Broken is fixed in the shared helper before push.
3a. `node tools/avoid-ai-design/scripts/detect.mjs --min=P1 qa/preview/` on the rendered HTML (detect mode — it reports, you fix in the builder). For `redesign`/`new` pages: no P0, and no SD tell the spec didn't ask for. For `clone` pages: findings are logged in `qa/design-checklist.md` as advice only. A deliberate choice the spec asked for gets an `avoid-ai-design-ignore: <ID>` note in the spec so it isn't re-raised. Then apply the four success tests from the skill — justified, coherent, not a second-order default, consistent across pages — and the silhouette test: shrink the render to a block silhouette; if it could be any other product's page, the structure is the tell.
4. Faults: fix in `layout.py` / `build_template.py` / the shared section, regenerate all pages, re-run 1–3. If the fault could recur, add a check to an auditor.

**Exit:** both auditors pass on all templates; local render matches the spec; scanner clean at P0/P1 on redesign/new pages (or findings logged for clone pages).

---

## Stage 6 — Push

**Entry:** Stage 5 exit. Run from Adam's Mac unless the site's domain is on the org allowlist; a proxy block means run it on the Mac, not retry.

1. Media first: `push_core.py` uploads `assets/` through the `media` action (reused by name; JPEG/PNG converted to WebP, so the returned url is the one that goes in the JSON). `deploy/media-map.json` updated; templates regenerated with real ids and urls.
2. Page: `python3 deploy/push_core.py <tpl> "<Title>" <slug> [parent-slug]`. Auditors run first and stop on failure. Several pages: `--batch ops.json` (≤ 50 ops, in order).
3. Theme parts (header, footer, single post): `template` action with `type` and `conditions` (`include/general` etc.), then `conditions` to confirm which template wins each location.
3a. Menus: `menu` action (nested items, `location` from `status.menu_locations`).
4. FormCraft: import the `.txt` in wp-admin, open once and Save, record the id in `deploy/pages.json > forms`, regenerate the page with the shortcode.
5. `deploy/pages.json` updated by the script (append-only). Never hand-edit from an old copy.
6. `flush` (`push_core.py` does it) then purge the host cache. Wait 25 s. Warm the URL twice.

**Exit:** `python3 deploy/verify_live.py` confirms every pushed page renders.

---

## Stage 7 — Staging QA (one batched round, two at most)

**Entry:** Stage 6 exit.

1. `python3 build/capture_shots.py` at 1440/1024/390 (+768/880 read-only). `python3 build/qa_diff.py` for `clone` sections; `python3 build/responsive_audit.py` for `designed`/`new` sections.
2. Craft-floor checks and `qa/design-checklist.md` ticked in the same round. Save each staging page's HTML to `qa/staging-html/` and run `node tools/avoid-ai-design/scripts/detect.mjs --min=P1 qa/staging-html/` on it (Elementor and the theme can reintroduce tells the local render didn't have: default-kit fonts, untouched radius, icon chips). Optional: Impeccable detector on the same folder.
3. Contact sweep: tap every `tel:` and submit every form on staging; notification received.
4. Fix at source (Stage 5 loop), re-push (Stage 6), one more round. Then stop.

**Exit:** clone sections < 2 % RMSE at all widths; designed sections pass the rules; design checklist ticked; every form delivers.

---

## Stage 8 — SEO

**Entry:** Stage 7 exit.

1. Titles, descriptions, focus keyword, canonical, noindex and og_image for every page in `spec/seo/<slug>.json`; re-run `python3 deploy/push_core.py <tpl> "<Title>" <slug>` with `SKIP_MEDIA=1` (the `page` action carries `seo`), then `--action '{"action":"meta","id":<id>}'` to read it back. Regulated clients: no rates, fees, LTVs, criteria.
2. H1/H2 hierarchy, alt text, slugs matching the live site (or redirect noted), canonical, OG, schema via the plugin.
3. Menus: the `menu` action (Stage 6, 3a) if not already done. No nav or breadcrumb pointing at a missing page.
4. `qa/seo-checklist.md` fully ticked.

**Exit:** checklist ticked; SEO 100 on PSI.

---

## Stage 9 — Performance loop

**Entry:** Stage 8 exit. Adam runs PSI; Claude never measures from the container.

1. Ask Adam for mobile + desktop scores and the top three Opportunities/Diagnostics. Log in `qa/psi.md`.
2. Fix the top item at source (fonts, LCP image, CSS loading, third-party, cache headers at host). Re-push, purge, wait, ask again.
3. Stop at 100/100, or when the only remaining item is outside WordPress (host cache headers, a client-mandated script) and it is written down.

**Exit:** `qa/psi.md` shows 100/100 or the named blocker.

---

## Stage 10 — Handover

**Entry:** Stage 9 exit.

1. `qa/build-report.md`: overview, pipeline, pages table with IDs, performance runs, responsive passes, channels, gotchas, ordered "where it stands" with the single blocking item first.
2. Commit the project folder if it is a git repo.
3. Closing message: what was built, page IDs, scores, deviations, what the client must supply (copy, photos, legal sign-off), what needs Adam's go-ahead.
4. Rotate any credential that was ever pasted into a chat. Website Core stays until go-live; on a build handed over for good, `CONFIRM_SELFDESTRUCT=yes python3 deploy/push_core.py --selfdestruct` only on Adam's explicit go-ahead.

**Exit:** report written; Adam has the closing message.

---

## Stage 11 — Go-live (separate task, on Adam's instruction)

1. Client sign-off on legal pages and any sample copy; banners removed; `[CLIENT TO CONFIRM]` resolved.
2. Slugs and redirects match the live site. Conversion tracking on forms and `tel:` if there is ad spend.
3. Domain pointed; `noindex` removed (`settings` `search_visible: true`); sitemap submitted; cache purged; PSI re-run on the live URL and logged.
4. On Adam's go-ahead: `CONFIRM_SELFDESTRUCT=yes python3 deploy/push_core.py --selfdestruct` (or Adam removes the plugin in wp-admin). Website Core never stays on a live site.

---

## Stage 12 — Retrospective and self-heal (after sign-off, every project, no exceptions)

**Entry:** Stage 11 exit (client sign-off and go-live), or Adam declares the project complete.

The build report (Stage 10) says *what* was built. This stage says *what we learned* and, more importantly, turns every lesson into a change in the kit so the next build cannot repeat the mistake. A lesson that only lives in a document is not learned.

1. **Gather the evidence, don't recall it.** Read `qa/build-report.md`, `qa/psi.md`, every `qa/<page>.md` tick list, `qa/design-checklist.md`, the git log of the project folder (`git log --oneline`), and the session notes. Count: pages built, pushes per page, staging QA rounds per page, auditor failures caught before push, Gate B items raised, credentials rotated, days from intake to sign-off.
2. **Write `qa/retro.md`** from `qa/retro-template.md`. Every entry in the "went wrong" and "lesson" sections has a source (a commit, a report line, a PSI run) — no impressions. Sections, in order: summary in five lines; the numbers from step 1; what went well and *why* (so it can be kept deliberately, not by luck); what went wrong, each with root cause, cost (time, pushes, credits, client impact) and where in the pipeline it should have been caught; what the client or Adam changed mid-build and whether the playbook handled it; what a smaller model would have got wrong here; the lessons table.
3. **Classify every lesson** into exactly one of four kinds, in the lessons table:
   - **Kit** — a script, helper or auditor change (`build/`, `deploy/`, `mu-plugins/`). The fault can be caught or prevented by code.
   - **Playbook** — a missing or mis-ordered step, a missing exit condition, a check that belonged at an earlier stage.
   - **Skill** — a standard, rule or threshold (spacing, craft floor, responsive rules, SEO, performance).
   - **One-off** — genuinely specific to this client or host; recorded in `LESSONS.md` for reference, changes nothing.
   Apply the test from the Expert Broker build: *would this have happened on the next client too?* If yes, it is not a one-off.
4. **Apply the Kit lessons now.** Make the change in `WEBSITE BUILDER STORAGE/Elementor-Claude-builder` (not in the client folder), with the auditor or test that proves it, and commit with a message that names the retro (`retro(<client>): audit_widths also checks mobile_extra`). Every fault that recurred or could recur gets a check in an auditor, or a hard failure in a helper, or a required field in `site.json` — whichever fails earliest.
5. **Apply the Playbook lessons now.** Edit `PLAYBOOK.md` in the kit: add the step, move the check earlier, tighten the exit condition. Commit.
6. **Propose the Skill lessons.** Standards live in the saved skill and only Adam can save it: edit `skills/elementor-clone-build/SKILL.md` in the kit, commit, and hand Adam a skill proposal with the diff summarised in one paragraph. Do not silently diverge the kit copy from the saved skill; the proposal is what closes the loop.
7. **Append to `LESSONS.md`** in the kit: one dated block per project — client, stack, the numbers, the lessons table with its kind and the commit that applied each. This is the running memory of the pipeline; read it at Stage 0 of every new build.
8. **Prune.** Anything in the playbook, skill or kit that this build proved unnecessary or wrong is removed or corrected, not left to accumulate. A rule nobody could point to a reason for is a candidate.
9. **Report to Adam** in one message: the five-line summary, the lessons table, the commits made, the skill proposal (if any), and one thing to watch on the next build. Push the kit to GitHub (`git push`) or ask Adam to.

**Exit:** `qa/retro.md` written; every non-one-off lesson has a commit in the kit or a skill proposal; `LESSONS.md` has this project's block; the kit is pushed.

**Self-heal during the build, not only after it.** The retro is the formal pass, but the same loop runs the moment a fault is found at any stage: name where it lives (page, shared helper, playbook, standard), fix it there, add the guard that would have caught it, note it in `qa/build-report.md` under "Gotchas". Stage 12 then checks that every gotcha in the report has a matching guard or lesson. A gotcha with no guard is the first item on the lessons table.

---

## Never

- Never build with an HTML widget, custom CSS, or PHP beyond the kit mu-plugin without Gate B approval.
- Never push, screenshot or measure from the cloud container.
- Never paste a credential, an `.env`, or a raw FormCraft export into chat.
- Never regenerate `deploy/pages.json` from an old copy.
- Never patch a single page's template for a fault that lives in a shared helper.
- Never leave a `[PLACEHOLDER]` in a template; the auditors exist so this cannot happen silently.
- Never write regulatory or legal wording; extract, parity-check, flag for sign-off.
- Never switch a page from clone to redesign without a Gate B note.
- Never keep polishing past the second staging QA round.
- Never close a project without Stage 12. A build report without a retro and kit commits is a build we will repeat.
- Never trade one default for another: the fix for a purple gradient is not cream-and-terracotta, and the fix for that is not near-black-and-lime. Every direction traces back to the client's subject and is checked against the SD clusters before Gate A.

## Per-page tick list (copy into `qa/<page>.md`)

```
[ ] spec written, mode set, Gate A approved
[ ] build_<page>.py uses layout.py + SP tokens only
[ ] audit_widths pass   [ ] audit_contact pass   [ ] render_preview reviewed
[ ] pushed; pages.json entry present; verify_live OK
[ ] qa_diff / responsive_audit pass at 1440/1024/390 (+768/880 read)
[ ] design-checklist ticked   [ ] avoid-ai-design scan: no P0/P1 (redesign/new) or logged (clone)
[ ] forms deliver; tel: links work
[ ] seo-checklist ticked; title/description pushed and read back
[ ] PSI logged in qa/psi.md
[ ] every gotcha for this page has a guard or a lessons-table entry (Stage 12)
```
