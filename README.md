# Elementor Claude Builder

Ignite Creative's kit for rebuilding a reference site or PDF as native Elementor (Flexbox Container) JSON, pushed to a 20i staging site with WP-CLI or the REST API, to a 100 PageSpeed / full-SEO standard.

- `skills/elementor-clone-build/SKILL.md` — the Claude skill (the procedure). Save it to your Claude account; this copy is the backup.
- `build/` — capture, generate, QA scripts (Playwright + Python).
- `deploy/` — push scripts. Copy `.env.example` to `.env` and fill in; `.env` is gitignored.
- `templates/`, `assets/`, `spec/`, `qa/`, `reference/` — per-client working folders (empty here).
- `tools/` — optional shallow clones of [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) and [impeccable](https://github.com/pbakaus/impeccable), gitignored.

New client: copy this folder to `~/Desktop/<Client>`, connect it to a Claude session, and start with the reference URL or PDF.
