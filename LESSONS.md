# Lessons — running memory of the pipeline

Read this at Stage 0 of every build. One block per project, newest first. Every lesson that is not a one-off has a commit or a skill proposal against it; if it doesn't, it is not learned yet.

---

## 2026-09-22 — The Expert Broker (mortgage broker; Squarespace → Elementor; nginx host, REST route)

Numbers: 17 pages; PSI 99 desktop / 89 mobile at handover; 3 responsive passes; 2 credentials rotated.

| # | Lesson | Kind | Applied in |
|---|---|---|---|
| 1 | Contact details are a Stage 0 input; 13 forms shipped to `[EMAIL ADDRESS]` | Kit + Playbook | `layout.py` requires `spec/site.json`; `audit_contact.py` gates every push |
| 2 | `col(w_t=100)` only stacks if the parent row stacks — 15 of 22 templates overflowed at tablet | Kit | `row()`/`col()` fixed in `layout.py`; `audit_widths.py` gates every push |
| 3 | Host profile before push route: nginx, no SSH, Imunify360 — `.htaccess` advice was wrong, container pushes 403'd | Playbook | Stage 0 host profile; Stage 6 "from the Mac, never the container" |
| 4 | `pages.json` rewritten from an old copy lost three pages | Kit + Playbook | append-only rule; scripts own the file |
| 5 | Credentials pasted into chat twice | Skill + Playbook | Rule 9; `deploy/.env` only |
| 6 | Site-wide settings (breakpoints, optimised CSS, mu-plugin) proposed at the end instead of switched on at the start | Playbook | Stage 1 |
| 7 | Clone drifted to redesign without a gate | Skill | Rule 8, `Mode:` in spec |
| 8 | Fixes in one page's template instead of the shared helper (overlay opacity) | Playbook | "fix at source" in Stages 5 and 7; Never list |
| 9 | Yoast silently discards REST meta writes without registration | Kit | mu-plugin; `push_seo.py` reads back |
| 10 | Screenshots < 25 s after a push measure an unstyled page | Playbook | Stage 6 step 6 |
