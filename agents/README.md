# The build team — one orchestrator, seven specialists

Why split: one agent carrying the whole skill (50 KB) plus a client's spec, tokens and QA output runs out of attention and credits fast, and makes design decisions while it is thinking about SSH. A specialist carries only its own standards and the files it needs, does one stage, and hands back a short result. The orchestrator carries the playbook and the gates, never the detail.

The spec files are the shared memory. Agents do not talk to each other; they read and write the project folder. That is deliberate: every hand-off is a file another agent (or Adam, or the next session) can read, and nothing lives only in one agent's context.

## Roles

| Agent | Owns (playbook stages) | Reads | Writes | Standards it carries |
|---|---|---|---|---|
| **orchestrator** | 0, 3 (Gate A message), 10, 12; sequencing of everything else | PLAYBOOK.md, LESSONS.md, every agent's result | `spec/site.json`, `qa/build-report.md`, `qa/retro.md`, `LESSONS.md` | The Playbook table, the nine rules, the Never list. Nothing else. |
| **capture** | 2 | reference URL/PDF | `reference/*`, `assets/*`, `assets/manifest.json` | Phase 1 (capture), legal parity rules |
| **design** | 3 (spec + direction) | `reference/*`, `spec/site.json`, LESSONS.md | `spec/<page>.md`, `qa/design-checklist.md` | Design Standards: Spacing Scale, Craft floor, Anti-AI design, Responsive Rules, UI UX Pro Max, widget mapping table |
| **build** | 4 | `spec/<page>.md`, `spec/site.json`, `deploy/media-map.json` | `build/build_<page>.py`, `templates/*.json`, `templates/forms/*.txt` | Generator conventions, schema skeleton, `layout.py`/`build_template.py` API, Forms |
| **qa** | 5, 7 | `templates/*`, `reference/*`, `spec/*`, staging URL | `qa/preview/*`, `qa/staging-html/*`, `qa/<page>.md` tick lists, diff reports | Auditors, `render_preview`, `detect.mjs`, `qa_diff`, `responsive_audit`, craft-floor checks, silhouette test |
| **deploy** | 1 (site setup), 6 | `templates/*`, `assets/*`, `deploy/.env` (sourced, never printed), `spec/site.json > host` | `deploy/pages.json`, `deploy/media-map.json`, staging site | Routes A/B/C, cache purge + 25 s wait, mu-plugin, breakpoints, theme-builder conditions. **Runs on Adam's Mac only.** |
| **seo** | 8 | `spec/*`, `content.json`, `deploy/pages.json`, live-site slugs | `deploy/seo.json`, `qa/seo-checklist.md`, SEO meta on staging (via deploy scripts) | Phase 5, regulated-client copy rules, slug parity, schema |
| **perf** | 9 | Adam's PSI paste, `qa/psi.md`, `spec/site.json > host` | `qa/psi.md`, `qa/perf-checklist.md`, fixes routed to build/deploy | Phase 6, font/LCP/CLS rules, cache-header facts per host |

## Sequencing and parallelism

```
0 orchestrator ─► 1 deploy (site setup) ─► 2 capture ─► 3 design ──STOP Gate A──► 4 build ─► 5 qa ─► 6 deploy ─► 7 qa ─► 8 seo ─┐
                                                                                                                              ├─► 10 orchestrator ─► 11 (Adam) ─► 12 orchestrator
                                                                                                                       9 perf ─┘
```

Parallel where it is safe and pays: **capture** runs one instance per page (independent URLs); **design** may run per page after the first page has fixed the direction (page one sets the contract, the rest inherit it — never in parallel with page one); **build** and **qa Stage 5** run per page; **seo** and **perf** run side by side after Stage 7. Never parallel: Stage 1, Gate A, Stage 6 pushes to the same site, Stage 12.

## Hand-off contract (every agent, every time)

Return to the orchestrator, in this order, under 300 words:

```
STAGE: <n> <name>            PAGE(S): <slugs or all>
STATUS: done | blocked | needs-gate-b
WROTE: <paths>
CHECKS: <auditor/scanner/diff results, one line each>
GATE B ITEMS: <none | list>
LESSONS: <none | one line each — anything that should change the kit, playbook or skill>
NEXT: <what the orchestrator should run>
```

Never paste file contents, JSON, CSS or screenshots into the result. Paths only. The orchestrator reads files when it needs to, and copies LESSONS into the build report's Gotchas so Stage 12 finds them.

## Model tiers (credit rule)

Judgement stages — **design**, **orchestrator at Gate A and Stage 12**, **qa Stage 7 (visual)** — run on the strongest model available. Mechanical stages — **capture**, **build** (spec → code), **qa Stage 5** (auditors, scanner), **deploy**, **seo** (from an approved spec), **perf** (from a PSI paste) — run on a mid-tier model. Nothing runs on a small model without a spec to follow and an auditor to catch it.

## What each agent must never do

- Make a decision another agent owns (build does not change the direction; seo does not change layout; qa does not fix, it reports — the fix goes back to build or design).
- Skip its exit condition because the orchestrator seems in a hurry.
- Read the whole skill. Each brief names the sections it carries; that is all it loads.
- Touch `deploy/.env` (deploy sources it; nobody prints it) or push from the cloud container.
