# Elementor Claude Builder

Ignite Creative's kit for rebuilding a reference site or PDF as native Elementor (Flexbox Container) JSON, pushed to a 20i staging site with WP-CLI or the REST API, to a 100 PageSpeed / full-SEO standard.

- `PLAYBOOK.md` — the stage-by-stage order of operations with entry/exit checks; followed on every build.
- `skills/elementor-clone-build/SKILL.md` — the Claude skill (the procedure). Save it to your Claude account; this copy is the backup.
- `build/` — capture, generate, QA scripts (Playwright + Python). `layout.py` holds the shared row/col/section helpers and loads contact details from `spec/site.json`; `audit_widths.py` and `audit_contact.py` gate every push; `render_preview.py` renders JSON to static HTML for local QA; `build_form.py` generates FormCraft import files.
- `deploy/` — push scripts (SSH+WP-CLI or REST). Copy `.env.example` to `.env` and fill in; `.env` is gitignored and never pasted into chat. `mu-plugins/ignite-site-fixes.php` is the per-site must-use plugin (landmark, skip link, Yoast REST, LCP preload, font trimming).
- `templates/`, `assets/`, `spec/`, `qa/`, `reference/` — per-client working folders (empty here).
- `tools/` — optional shallow clones of [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) and [impeccable](https://github.com/pbakaus/impeccable), gitignored.

New client: copy this folder to `~/Desktop/<Client>`, fill in `spec/site.json` (contact details + host profile) from `spec/site.example.json`, connect the folder to a Claude session, and start with the reference URL or PDF.
