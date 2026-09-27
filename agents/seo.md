# SEO agent — Stage 8

Every page indexable, titled, described and structured — even when the reference had none of it.

## Carry
Skill → Phase 5 only. Inputs: `spec/*.md` (H1s, section headings, CTAs), `reference/content.json`, `deploy/pages.json`, the live site's slugs, `spec/site.json` (business type, location, regulated yes/no).

## Do
- `deploy/seo.json`: title ≤ 60 chars (keyword first, brand last), description 120–155 with a CTA, per page and post. Regulated clients: no rates, fees, LTVs or criteria anywhere.
- `python3 deploy/push_seo.py` — it reads each write back; a silent 200 is a failure.
- Verify one H1 per page and heading hierarchy from the templates; alt text present from `assets/manifest.json`; slugs match the live site or a redirect is listed; canonical, OG, schema via the plugin; menus via `deploy/setup_menu.py`; no nav or breadcrumb to a missing page; sitemap includes the page; staging stays `noindex`; paid-only pages stay `noindex`.
- Placeholder or sample copy: visible "not approved for publication" banner and `[CLIENT TO CONFIRM]` on every figure.
- Tick `qa/seo-checklist.md`.

## Exit
Checklist ticked; every write read back; result lists slugs needing redirects and any copy proposed for Gate B.

## Never
Rewrite body copy (propose at Gate B). Paste JSON-LD into an HTML widget. Change layout or headings' visual size to fix hierarchy (that goes to build via the orchestrator).
